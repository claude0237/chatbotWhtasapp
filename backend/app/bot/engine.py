"""BotEngine — processes incoming WhatsApp messages and returns the appropriate response"""
import re
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Sentinel prefix embedded in the return value when a handoff step fires.
# Format: "__HANDOFF__:<message to send to client>"
# The webhook layer detects this prefix and changes conversation status to WAITING.
HANDOFF_PREFIX = "__HANDOFF__:"

from app.bot.models import BotConversationState, BotType, FallbackStrategy
from app.bot.repositories import (
    BotConfigurationRepository,
    BotKeywordRepository,
    BotScenarioRepository,
    BotConversationStateRepository,
)
from app.products.repositories import ProductRepository, ProductCategoryRepository
from app.companies.models import Company, SubscriptionPlan, MLQuota, MLUsage
from app.config import settings


class BotEngine:
    """
    Core engine that decides what to reply to an incoming message.

    Priority order:
      1. Contact is mid-scenario  → advance the scenario
      2. Message matches a scenario trigger_keyword  → start the scenario
      3. Message matches a keyword  → return keyword response
      4. Fallback  → return unknown_message from BotConfiguration
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config_repo = BotConfigurationRepository(db)
        self.keyword_repo = BotKeywordRepository(db)
        self.scenario_repo = BotScenarioRepository(db)
        self.state_repo = BotConversationStateRepository(db)
        self.product_repo = ProductRepository(db)
        self.category_repo = ProductCategoryRepository(db)

    async def process(
        self,
        company_id: UUID,
        phone_number: str,
        message_text: str,
    ) -> Optional[str]:
        """
        Process one incoming message.
        Returns the text to send back, or None if no bot is configured.
        """
        config = await self.config_repo.get_by_company_id(company_id)
        if not config:
            return None

        # Check if ML is enabled for the company and verify subscription plan
        company_result = await self.db.execute(select(Company).where(Company.id == company_id))
        company = company_result.scalar_one_or_none()
        
        # ML is only available for non-FREE plans
        # Superadmin enables ML at company level (company.ml_enabled)
        # Company admin then chooses bot mode: NATIVE, ML, or HYBRID
        ml_enabled = company.ml_enabled if company else False
        can_use_ml = ml_enabled and company and company.subscription_plan != SubscriptionPlan.FREE

        normalized = message_text.strip().upper()

        # ── 1. Active scenario mid-flight? ──────────────────────────────────
        state = await self.state_repo.get_active(company_id, phone_number)
        if state:
            return await self._advance_scenario(state, normalized, message_text, config.unknown_message)

        # ── 2. Scenario trigger? ─────────────────────────────────────────────
        scenario = await self.scenario_repo.get_by_trigger_keyword(config.id, normalized)
        if scenario and scenario.steps:
            first_step = scenario.steps[0]
            first_message = await self._resolve_step_message(first_step, {}, company_id)
            new_state = BotConversationState(
                company_id=company_id,
                phone_number=phone_number,
                scenario_id=scenario.id,
                current_step=0,
                collected_data={},
                retry_count=0,
                last_bot_message=first_message,
            )
            await self.state_repo.create(new_state)
            return first_message

        # ── 3. Keyword match? ────────────────────────────────────────────────
        keyword_obj = await self.keyword_repo.get_by_keyword(config.id, normalized)
        if keyword_obj:
            return self._interpolate(keyword_obj.response, {})

        # ── 4. ML Processing (if enabled, configured, and plan allows) ──────────
        if can_use_ml and config.bot_type != BotType.NATIVE:
            # Check ML quota before processing
            if not await self._check_and_update_ml_usage(company_id, company):
                # Quota exceeded, fall back to native
                return self._interpolate(config.unknown_message or "Je n'ai pas compris votre message.", {})
            
            try:
                from app.ml.engine import MLEngine
                ml_engine = MLEngine(self.db)
                
                native_response = self._interpolate(config.unknown_message or "Je n'ai pas compris votre message.", {})
                
                # Use platform default ML configuration
                ml_result = await ml_engine.process_message(
                    company_id, 
                    message_text,
                    temperature=settings.ml_default_temperature,
                    max_tokens=settings.ml_default_max_tokens,
                    confidence_threshold=settings.ml_default_confidence_threshold
                )
                
                logger.info(f"ML result: {ml_result}")
                
                # Check confidence threshold
                if ml_result.get("confidence", 0) >= settings.ml_default_confidence_threshold:
                    return ml_result.get("response", native_response)
                else:
                    # Fallback to native if confidence is low
                    logger.info(f"ML confidence too low: {ml_result.get('confidence', 0)} < {settings.ml_default_confidence_threshold}")
                    return native_response
            except Exception as e:
                # If ML fails, fall back to native
                logger.error(f"ML processing failed: {str(e)}")
                pass

        # ── 5. Native Fallback ──────────────────────────────────────────────
        return self._interpolate(config.unknown_message or "Je n'ai pas compris votre message.", {})

    async def _check_and_update_ml_usage(self, company_id: UUID, company: Company) -> bool:
        """Check ML quota and update usage. Returns True if allowed, False if quota exceeded."""
        # Get quota for company's plan
        quota_result = await self.db.execute(select(MLQuota).where(MLQuota.plan == company.subscription_plan))
        quota = quota_result.scalar_one_or_none()
        
        if not quota:
            return False
        
        # Unlimited quota
        if quota.monthly_requests == -1:
            return True
        
        # Get or create usage record
        now = datetime.utcnow()
        current_month = now.year * 100 + now.month
        
        usage_result = await self.db.execute(select(MLUsage).where(MLUsage.company_id == company_id))
        usage = usage_result.scalar_one_or_none()
        
        if not usage:
            usage = MLUsage(
                company_id=company_id,
                monthly_requests=0,
                daily_requests=0,
                total_requests=0,
                current_month=current_month,
                current_day=now.date(),
                created_at=now,
                updated_at=now,
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)
        
        # Reset counters if period changed
        if usage.current_month != current_month:
            usage.monthly_requests = 0
            usage.current_month = current_month
        
        if usage.current_day != now.date():
            usage.daily_requests = 0
            usage.current_day = now.date()
        
        # Check monthly quota
        if usage.monthly_requests >= quota.monthly_requests:
            return False
        
        # Check daily quota if set
        if quota.daily_requests and usage.daily_requests >= quota.daily_requests:
            return False
        
        # Update usage
        usage.monthly_requests += 1
        usage.daily_requests += 1
        usage.total_requests += 1
        usage.updated_at = now
        await self.db.commit()
        
        return True

    async def _advance_scenario(
        self,
        state: BotConversationState,
        normalized: str,
        raw_text: str,
        unknown_message: Optional[str],
    ) -> str:
        """
        Evaluate the current step against the user's answer, then move forward.

        Step types supported (field "type" in the step JSON):
          - "text"      (default) : linear, advance unconditionally
          - "choice"    : dict "choices" keyed by uppercase answer (+ "DEFAULT")
          - "condition" : list "conditions" with if/value/reply entries
        """
        scenario = state.scenario
        steps = scenario.steps if scenario else []
        current_step = steps[state.current_step] if state.current_step < len(steps) else {}

        # Save raw answer (1-based to match UI step numbering)
        step_key = f"step_{state.current_step + 1}_answer"
        state.collected_data = {**state.collected_data, step_key: raw_text}
        state.retry_count = 0  # client responded → reset follow-up counter

        step_type = current_step.get("type", "text")

        # ── Catalogue step: inject product list then advance ─────────────────
        if step_type == "catalogue":
            cat_name = current_step.get("catalogue_category") or None
            raw_prefix = self._interpolate(current_step.get("message", "") or "", state.collected_data)
            prefix = await self._resolve_catalogue_vars(raw_prefix, state.company_id) if raw_prefix else ""
            catalogue_text = await self._build_catalogue_text(state.company_id, cat_name)
            full_reply = (prefix + "\n\n" + catalogue_text).strip() if prefix else catalogue_text

            next_index = state.current_step + 1
            state.current_step = next_index
            if state.current_step >= len(steps):
                await self.state_repo.delete(state)
            else:
                state.last_bot_message = full_reply
                await self.state_repo.update(state)
            return full_reply

        # ── Handoff step: transfer to human agent ────────────────────────────
        if step_type == "handoff":
            await self.state_repo.delete(state)
            handoff_msg = current_step.get("message") or "Un agent va prendre en charge votre demande. Merci de patienter."
            return f"{HANDOFF_PREFIX}{self._interpolate(handoff_msg, state.collected_data)}"

        # ── Evaluate conditional reply (inline — does NOT advance step) ─────
        conditional_reply = self._evaluate_step(current_step, normalized, step_type)
        if conditional_reply is not None:
            # The step produced an inline reply for invalid input → stay on same step
            await self.state_repo.update(state)
            raw = self._interpolate(conditional_reply, state.collected_data)
            return await self._resolve_catalogue_vars(raw, state.company_id)

        # ── Determine next step index ────────────────────────────────────────
        next_index = self._next_step_index(current_step, normalized, state.current_step, steps)

        state.current_step = next_index

        if state.current_step >= len(steps):
            # Scenario finished
            await self.state_repo.delete(state)
            # For choice/condition steps, use the branch-specific reply first,
            # then optionally append the generic end_message.
            resolved = self._resolve_reply(current_step, normalized, step_type)
            end_msg = current_step.get("end_message") or current_step.get("closing")
            if resolved and end_msg:
                raw_reply = self._interpolate(resolved, state.collected_data)
                resolved_reply = await self._resolve_catalogue_vars(raw_reply, state.company_id)
                raw_end = self._interpolate(end_msg, state.collected_data)
                resolved_end = await self._resolve_catalogue_vars(raw_end, state.company_id)
                return f"{resolved_reply}\n\n{resolved_end}"
            if resolved:
                raw = self._interpolate(resolved, state.collected_data)
                return await self._resolve_catalogue_vars(raw, state.company_id)
            if end_msg:
                raw = self._interpolate(end_msg, state.collected_data)
                return await self._resolve_catalogue_vars(raw, state.company_id)
            return "✅ Merci !"

        next_step = steps[state.current_step]
        next_message = await self._resolve_step_message(next_step, state.collected_data, state.company_id)
        state.last_bot_message = next_message
        await self.state_repo.update(state)

        # If the current branch had a reply (choice/condition), prepend it to the next step message
        branch_reply = self._resolve_reply(current_step, normalized, step_type)
        if branch_reply:
            raw = self._interpolate(branch_reply, state.collected_data)
            resolved_branch = await self._resolve_catalogue_vars(raw, state.company_id)
            return f"{resolved_branch}\n\n{next_message}"

        return next_message

    # ── Catalogue helpers ────────────────────────────────────────────────────

    async def _build_catalogue_text(self, company_id: UUID, category_name: Optional[str] = None) -> str:
        """Build a formatted product list for WhatsApp from catalogue."""
        if category_name:
            cats = await self.category_repo.get_by_company_id(company_id)
            cat = next((c for c in cats if c.name.upper() == category_name.strip().upper()), None)
            products = await self.product_repo.get_by_category_id(cat.id, active_only=True) if cat else []
        else:
            products = await self.product_repo.get_by_company_id(company_id, active_only=True, limit=20)

        if not products:
            return "Aucun produit disponible pour le moment."

        lines = ["🛍️ *Nos produits :*\n"]
        for p in products:
            stock_label = f"({p.stock} en stock)" if p.stock > 0 else "_(Rupture)_"
            lines.append(f"• *{p.name}* — {p.price} {p.currency} {stock_label}")
            if p.description:
                lines.append(f"  _{p.description[:80]}{'…' if len(p.description) > 80 else ''}_")
        return "\n".join(lines)

    async def _build_product_card(self, company_id: UUID, product_name: str) -> str:
        """Build a detailed product card for a specific product."""
        products = await self.product_repo.search(company_id, product_name, limit=1, active_only=True)
        if not products:
            return f"Produit *{product_name}* introuvable dans notre catalogue."
        p = products[0]
        stock_label = f"{p.stock} en stock" if p.stock > 0 else "Rupture de stock"
        card = f"🛍️ *{p.name}*\n"
        if p.description:
            card += f"\n{p.description}\n"
        card += f"\n💰 Prix : *{p.price} {p.currency}*"
        card += f"\n📦 Stock : {stock_label}"
        if p.images:
            card += f"\n🖼️ {p.images[0]}"
        return card

    async def _resolve_catalogue_vars(self, text: str, company_id: UUID) -> str:
        """Resolve {catalogue}, {catalogue:Cat}, {produit:Nom} placeholders."""
        import re as _re
        # {catalogue:NomCat} or {catalogue}
        async def replace_cat(m):
            cat_name = m.group(1).strip() if m.group(1) else None
            return await self._build_catalogue_text(company_id, cat_name)

        # Manual async substitution for {catalogue:X} and {catalogue}
        pattern_cat = _re.compile(r'\{catalogue(?::([^}]+))?\}')
        result = text
        for m in list(pattern_cat.finditer(text)):
            replacement = await replace_cat(m)
            result = result.replace(m.group(0), replacement, 1)

        # {produit:NomProduit}
        pattern_prod = _re.compile(r'\{produit:([^}]+)\}')
        for m in list(pattern_prod.finditer(result)):
            replacement = await self._build_product_card(company_id, m.group(1).strip())
            result = result.replace(m.group(0), replacement, 1)

        return result

    async def _resolve_step_message(self, step: dict, collected: dict, company_id: UUID) -> str:
        """Extract step message, interpolate vars and resolve catalogue placeholders."""
        raw = self._interpolate(self._extract_step_message(step), collected)
        return await self._resolve_catalogue_vars(raw, company_id)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _evaluate_step(self, step: dict, normalized: str, step_type: str) -> Optional[str]:
        """
        For choice/condition steps: if the answer is invalid return an error reply
        so the user stays on the same step. Returns None if the answer is valid.
        """
        if step_type == "choice":
            choices: dict = step.get("choices", {})
            key = normalized.strip()
            if key in choices:
                return None  # valid choice → advance
            if "DEFAULT" in choices:
                return choices["DEFAULT"]  # invalid → re-ask
            return None  # no DEFAULT defined → advance anyway

        if step_type == "condition":
            conditions: list = step.get("conditions", [])
            for cond in conditions:
                if self._match_condition(cond, normalized):
                    return None  # matched → advance
            # No match and no DEFAULT → advance anyway
            for cond in conditions:
                if cond.get("if") == "default":
                    return cond.get("reply", "")
            return None

        return None  # "text" step is always valid

    def _resolve_reply(self, step: dict, normalized: str, step_type: str) -> Optional[str]:
        """Return the reply text for a matched choice/condition (used as closing message)."""
        if step_type == "choice":
            choices: dict = step.get("choices", {})
            return choices.get(normalized.strip()) or choices.get("DEFAULT")

        if step_type == "condition":
            conditions: list = step.get("conditions", [])
            for cond in conditions:
                if self._match_condition(cond, normalized):
                    return cond.get("reply", "")
            for cond in conditions:
                if cond.get("if") == "default":
                    return cond.get("reply", "")

        return None

    def _next_step_index(self, step: dict, normalized: str, current_idx: int, steps: list) -> int:
        """
        Determine the next step index.
        choice/condition steps can specify a "next_step" override per branch.
        """
        step_type = step.get("type", "text")

        if step_type == "choice":
            choices: dict = step.get("choices", {})
            branch = choices.get(normalized.strip(), {})
            if isinstance(branch, dict) and "next_step" in branch:
                target = branch["next_step"]
                idx = self._find_step_index(steps, target)
                if idx is not None:
                    return idx

        if step_type == "condition":
            conditions: list = step.get("conditions", [])
            for cond in conditions:
                if self._match_condition(cond, normalized):
                    if "next_step" in cond:
                        idx = self._find_step_index(steps, cond["next_step"])
                        if idx is not None:
                            return idx

        # Default: advance linearly
        return current_idx + 1

    @staticmethod
    def _match_condition(cond: dict, normalized: str) -> bool:
        """Evaluate a single condition entry against the normalized user input."""
        op = cond.get("if", "default")
        value = str(cond.get("value", "")).strip().upper()
        if op == "equals":
            return normalized == value
        if op == "contains":
            return value in normalized
        if op == "starts_with":
            return normalized.startswith(value)
        if op == "not_equals":
            return normalized != value
        if op == "default":
            return True
        return False

    @staticmethod
    def _find_step_index(steps: list, target) -> Optional[int]:
        """Find the 0-based index of a step by its 'step' number or by index."""
        for i, s in enumerate(steps):
            if isinstance(s, dict) and s.get("step") == target:
                return i
        # Fallback: treat target as 0-based index
        if isinstance(target, int) and 0 <= target < len(steps):
            return target
        return None

    @staticmethod
    def _interpolate(text: str, collected: dict) -> str:
        """
        Replace placeholders in text with collected data or built-in variables.

        Supported placeholders:
          {step_N_answer}  — answer collected at step N (0-based)
          {now}            — current datetime  e.g. 06/07/2026 11:45
          {date}           — current date only  e.g. 06/07/2026
          {time}           — current time only  e.g. 11:45
        """
        if not text or '{' not in text:
            return text

        now = datetime.now()
        built_in = {
            'now':  now.strftime('%d/%m/%Y %H:%M'),
            'date': now.strftime('%d/%m/%Y'),
            'time': now.strftime('%H:%M'),
        }

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            if key in built_in:
                return built_in[key]
            if key in collected:
                return str(collected[key])
            return match.group(0)  # unknown placeholder → keep as-is

        return re.sub(r'\{(\w+)\}', replacer, text)

    @staticmethod
    def _extract_step_message(step: dict) -> str:
        """Extract the display message from a step dict."""
        return step.get("message") or step.get("text") or str(step)
