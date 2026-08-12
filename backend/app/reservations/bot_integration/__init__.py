"""Reservation Bot Integration - Propose reservations, check availability, auto-confirm"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.reservations.services import ReservationService


RESERVATION_KEYWORDS = [
    "réserver", "réservation", "réservations", "rendez-vous", "rdv",
    "disponible", "disponibilité", "créneau", "créneaux", "booking",
    "prendre rendez-vous", "planifier", "programmer"
]

AVAILABILITY_KEYWORDS = [
    "disponible", "disponibilité", "dispo", "créneau", "créneaux",
    "quand", "horaire", "heure", "date"
]


class ReservationBotIntegration:
    """Integration between bot engine and reservation system"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.reservation_service = ReservationService(db)

    async def handle_reservation_query(
        self,
        company_id: UUID,
        message: str,
        customer_id: Optional[UUID] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Main entry point: detect reservation intent and respond"""
        message_lower = message.lower()

        is_reservation = any(kw in message_lower for kw in RESERVATION_KEYWORDS)
        if not is_reservation:
            return None

        # Check if context has a pending reservation flow
        if conversation_context:
            pending = conversation_context.get("pending_reservation")
            if pending:
                return await self._handle_reservation_flow(
                    company_id, message, pending, customer_id, conversation_context
                )

        # Check availability query
        is_availability = any(kw in message_lower for kw in AVAILABILITY_KEYWORDS)
        if is_availability:
            return await self._propose_available_slots(company_id)

        # Default: show services
        return await self._list_services(company_id)

    async def _list_services(self, company_id: UUID) -> str:
        """List available services for booking"""
        services = await self.reservation_service.get_company_services(company_id, active_only=True)

        if not services:
            return "Nous n'avons pas de services de réservation disponibles pour le moment."

        lines = ["📅 *Nos services disponibles :*\n"]
        for service in services:
            duration_str = f"{service.duration} min"
            price_str = f" - {service.price}€" if service.price else ""
            lines.append(f"• *{service.name}*{price_str} ({duration_str})")
            if service.description:
                lines.append(f"  _{service.description}_")

        lines.append("\nPour réserver, répondez avec le nom du service souhaité.")
        return "\n".join(lines)

    async def _propose_available_slots(self, company_id: UUID) -> str:
        """Show next available slots across all services"""
        services = await self.reservation_service.get_company_services(company_id, active_only=True)

        if not services:
            return "Aucun service disponible pour le moment."

        now = datetime.utcnow()
        next_7_days = now + timedelta(days=7)

        lines = ["🗓️ *Créneaux disponibles cette semaine :*\n"]
        has_slots = False

        for service in services[:3]:  # limit to 3 services
            slots = await self.reservation_service.get_available_slots(
                service.id, from_date=now, to_date=next_7_days
            )
            if slots:
                has_slots = True
                lines.append(f"*{service.name}*")
                for slot in slots[:3]:  # max 3 slots per service
                    start = datetime.fromisoformat(str(slot.start_time))
                    lines.append(
                        f"  • {start.strftime('%a %d/%m à %H:%M')}"
                    )

        if not has_slots:
            return "Aucun créneau disponible cette semaine. Contactez-nous pour plus d'informations."

        lines.append("\nPour réserver un créneau, indiquez le service et l'horaire souhaité.")
        return "\n".join(lines)

    async def _handle_reservation_flow(
        self,
        company_id: UUID,
        message: str,
        pending: Dict[str, Any],
        customer_id: Optional[UUID],
        context: Dict[str, Any]
    ) -> str:
        """Handle multi-step reservation flow from context"""
        step = pending.get("step")

        if step == "confirm":
            message_lower = message.lower()
            if any(w in message_lower for w in ["oui", "ok", "confirme", "yes", "d'accord", "valider"]):
                return await self._auto_confirm(company_id, pending, customer_id, context)
            elif any(w in message_lower for w in ["non", "annule", "no", "annuler"]):
                context.pop("pending_reservation", None)
                return "Réservation annulée. Comment puis-je vous aider ?"

        return await self._propose_available_slots(company_id)

    async def _auto_confirm(
        self,
        company_id: UUID,
        pending: Dict[str, Any],
        customer_id: Optional[UUID],
        context: Dict[str, Any]
    ) -> str:
        """Automatically create and confirm a reservation"""
        try:
            service_id = pending.get("service_id")
            slot_id = pending.get("slot_id")

            if not service_id or not slot_id:
                return "Informations manquantes pour finaliser la réservation."

            reservation = await self.reservation_service.create_reservation(
                company_id=company_id,
                service_id=service_id,
                slot_id=slot_id,
                customer_id=customer_id,
                notes=pending.get("notes")
            )

            # Auto-confirm
            reservation = await self.reservation_service.confirm_reservation(reservation.id)

            context.pop("pending_reservation", None)

            return (
                f"✅ *Réservation confirmée !*\n\n"
                f"Votre réservation a été enregistrée avec succès.\n"
                f"Référence : #{str(reservation.id)[:8].upper()}\n\n"
                f"Vous recevrez une confirmation par message."
            )

        except ValueError as e:
            return f"Impossible de finaliser la réservation : {str(e)}"

    async def propose_reservation_for_service(
        self,
        company_id: UUID,
        service_name: str
    ) -> str:
        """Bot proposes available slots for a specific service by name"""
        services = await self.reservation_service.get_company_services(company_id, active_only=True)

        matched = next(
            (s for s in services if service_name.lower() in s.name.lower()),
            None
        )

        if not matched:
            service_list = ", ".join(s.name for s in services)
            return f"Service non trouvé. Services disponibles : {service_list}"

        now = datetime.utcnow()
        slots = await self.reservation_service.get_available_slots(
            matched.id,
            from_date=now,
            to_date=now + timedelta(days=14)
        )

        if not slots:
            return f"Aucun créneau disponible pour *{matched.name}* dans les 2 prochaines semaines."

        lines = [f"📅 *Créneaux disponibles pour {matched.name} :*\n"]
        for slot in slots[:5]:
            start = datetime.fromisoformat(str(slot.start_time))
            end = datetime.fromisoformat(str(slot.end_time))
            lines.append(
                f"• {start.strftime('%A %d/%m à %H:%M')} → {end.strftime('%H:%M')}"
            )

        lines.append("\nRépondez avec l'horaire souhaité pour confirmer votre réservation.")
        return "\n".join(lines)
