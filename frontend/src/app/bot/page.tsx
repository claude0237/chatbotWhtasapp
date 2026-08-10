'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useHashTab } from '../../hooks/useHashTab';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';
import { productsService, ProductCategory } from '../../services/products';

interface BotConfiguration {
  id: string; company_id: string; bot_type: string; name: string;
  welcome_message: string | null; away_message: string | null;
  closing_message: string | null; unknown_message: string | null;
  language: string; timezone: string; avatar_url: string | null;
  native_rules: object | null; business_hours: Record<string, {open: string; close: string} | null> | null;
  ml_enabled: boolean | null; ml_provider: string | null; ml_model: string | null;
  ml_temperature: string | null; ml_max_tokens: number | null;
  fallback_strategy: string | null; confidence_threshold: string | null;
  created_at: string; updated_at: string;
}
interface BotScenario {
  id: string; bot_configuration_id: string; name: string;
  trigger_keyword: string; steps: any[]; is_active: boolean;
  created_at: string; updated_at: string;
}
interface BotKeyword {
  id: string; bot_configuration_id: string; keyword: string;
  response: string; category: string | null; created_at: string; updated_at: string;
}
interface SimMessage { role: 'user' | 'bot'; text: string; }

type StepType = 'text' | 'choice' | 'condition' | 'handoff' | 'catalogue';

const TIMEZONES = [
  { value: 'Africa/Douala', label: 'Afrique Centrale (Douala, Yaoundé) UTC+1' },
  { value: 'Africa/Lagos', label: 'Afrique de l\'Ouest (Lagos) UTC+1' },
  { value: 'Africa/Casablanca', label: 'Maroc (Casablanca) UTC+1' },
  { value: 'Africa/Tunis', label: 'Tunisie (Tunis) UTC+1' },
  { value: 'Africa/Abidjan', label: 'Côte d\'Ivoire (Abidjan) UTC+0' },
  { value: 'Africa/Accra', label: 'Ghana (Accra) UTC+0' },
  { value: 'Africa/Nairobi', label: 'Afrique de l\'Est (Nairobi) UTC+3' },
  { value: 'Africa/Johannesburg', label: 'Afrique du Sud (Johannesburg) UTC+2' },
  { value: 'Europe/Paris', label: 'France (Paris) UTC+1 / UTC+2' },
  { value: 'Europe/Brussels', label: 'Belgique (Bruxelles) UTC+1 / UTC+2' },
  { value: 'Europe/Zurich', label: 'Suisse (Zurich) UTC+1 / UTC+2' },
  { value: 'Europe/London', label: 'Royaume-Uni (Londres) UTC+0 / UTC+1' },
  { value: 'America/Montreal', label: 'Canada (Montréal) UTC-5 / UTC-4' },
  { value: 'America/New_York', label: 'États-Unis (New York) UTC-5 / UTC-4' },
  { value: 'America/Los_Angeles', label: 'États-Unis (Los Angeles) UTC-8 / UTC-7' },
  { value: 'Asia/Dubai', label: 'Émirats Arabes Unis (Dubaï) UTC+4' },
  { value: 'Asia/Singapore', label: 'Singapour UTC+8' },
  { value: 'UTC', label: 'UTC' },
];
interface ChoiceEntry { key: string; reply: string; }
interface ConditionEntry { if: 'equals' | 'contains' | 'starts_with' | 'not_equals' | 'default'; value: string; reply: string; }
interface StepDraft {
  type: StepType;
  message: string;
  end_message: string;
  choices: ChoiceEntry[];
  conditions: ConditionEntry[];
  catalogue_category: string;
}

const BLANK_STEP: StepDraft = { type: 'text', message: '', end_message: '', choices: [{ key: '', reply: '' }], conditions: [{ if: 'equals', value: '', reply: '' }], catalogue_category: '' };

export default function BotPage() {
  const { user } = useAuth();
  const companyId: string | undefined = (user as any)?.company_id;
  const [config, setConfig]       = useState<BotConfiguration | null>(null);
  const [scenarios, setScenarios] = useState<BotScenario[]>([]);
  const [keywords, setKeywords]   = useState<BotKeyword[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [activeTab, setActiveTab] = useHashTab<'config' | 'scenarios' | 'keywords' | 'simulation'>('config');
  const [submitting, setSubmitting] = useState(false);

  const [showConfigModal,   setShowConfigModal]   = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [showKeywordModal,  setShowKeywordModal]  = useState(false);
  const [editingScenario,   setEditingScenario]   = useState<BotScenario | null>(null);
  const [editingKeyword,    setEditingKeyword]    = useState<BotKeyword | null>(null);

  const [configForm,   setConfigForm]   = useState({ name: '', welcome_message: '', away_message: '', closing_message: '', unknown_message: '', language: 'fr', timezone: 'Africa/Douala', bot_type: 'NATIVE', followup_timeout_minutes: 60, followup_max_retries: 3, business_hours: null as Record<string, {open: string; close: string} | null> | null, ml_enabled: false, ml_provider: '', ml_model: '', ml_temperature: '', ml_max_tokens: 500, fallback_strategy: '', confidence_threshold: '' });
  const [companyMLEnabled, setCompanyMLEnabled] = useState(false);
  const [companyPlan, setCompanyPlan] = useState('FREE');
  const [scenarioForm, setScenarioForm] = useState({ name: '', trigger_keyword: '', is_active: true });
  const [scenarioSteps, setScenarioSteps] = useState<StepDraft[]>([{ ...BLANK_STEP }]);
  const [keywordForm,  setKeywordForm]  = useState({ keyword: '', response: '', category: '' });

  const [categories, setCategories] = useState<ProductCategory[]>([]);

  const [simMessages, setSimMessages] = useState<SimMessage[]>([]);
  const [simInput,    setSimInput]    = useState('');
  const simEndRef = useRef<HTMLDivElement>(null);

  // ── Simulation engine state ──────────────────────────────────────────────
  interface SimState { scenarioId: string; currentStep: number; collectedData: Record<string, string>; }
  const [simState, setSimState] = useState<SimState | null>(null);

  const simBuildCatalogueText = async (catName?: string): Promise<string> => {
    if (!companyId) return 'Aucun produit disponible.';
    try {
      const params: any = { active_only: true, limit: 20 };
      if (catName) params.category_name = catName;
      const r = await api.get(`/companies/${companyId}/products`, { params });
      const products: any[] = r.data;
      if (!products.length) return 'Aucun produit disponible pour le moment.';
      const lines = ['🛍️ *Nos produits :*\n'];
      for (const p of products) {
        const stock = p.stock > 0 ? `(${p.stock} en stock)` : '_(Rupture)_';
        lines.push(`• *${p.name}* — ${p.price} ${p.currency} ${stock}`);
        if (p.description) lines.push(`  _${p.description.slice(0, 80)}${p.description.length > 80 ? '…' : ''}_`);
      }
      return lines.join('\n');
    } catch {
      return 'Erreur de chargement du catalogue.';
    }
  };

  const simInterpolateAsync = async (text: string, data: Record<string, string>): Promise<string> => {
    if (!text || !text.includes('{')) return text;
    let result = text;
    const catMatches = [...result.matchAll(/\{catalogue:([^}]+)\}/g)];
    for (const m of catMatches) {
      const replacement = await simBuildCatalogueText(m[1]);
      result = result.replace(m[0], replacement);
    }
    if (result.includes('{catalogue}')) {
      const replacement = await simBuildCatalogueText();
      result = result.replace(/\{catalogue\}/g, replacement);
    }
    result = simInterpolate(result, data);
    return result;
  };

  const simInterpolate = (text: string, data: Record<string, string>): string => {
    if (!text || !text.includes('{')) return text;
    const now = new Date();
    const pad = (n: number) => n.toString().padStart(2, '0');
    const builtIn: Record<string, string> = {
      date: `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()}`,
      time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
      now: `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`,
    };
    return text.replace(/\{(\w+)\}/g, (match, key) => data[key] ?? builtIn[key] ?? match);
  };

  const simResolve = (text: string, data: Record<string, string>): Promise<string> =>
    text.includes('{catalogue') ? simInterpolateAsync(text, data) : Promise.resolve(simInterpolate(text, data));

  const simExtractMsg = (step: any): string => {
    if (!step) return '';
    if (step.type === 'catalogue') {
      const raw: string = step.message || '';
      const cat = step.catalogue_category || '';
      const cataloguePart = cat ? `{catalogue:${cat}}` : '{catalogue}';
      const prefix = raw && !raw.includes('{catalogue') ? raw + '\n\n' : '';
      return prefix + cataloguePart;
    }
    return step?.message || step?.text || JSON.stringify(step);
  };

  const simMatchCondition = (cond: any, normalized: string): boolean => {
    const op = cond.if || 'default';
    const val = String(cond.value || '').trim().toUpperCase();
    if (op === 'equals')      return normalized === val;
    if (op === 'contains')    return normalized.includes(val);
    if (op === 'starts_with') return normalized.startsWith(val);
    if (op === 'not_equals')  return normalized !== val;
    if (op === 'default')     return true;
    return false;
  };

  const simNextIndex = (step: any, normalized: string, currentIdx: number, steps: any[]): number => {
    const type = step?.type || 'text';
    if (type === 'choice') {
      const branch = step.choices?.[normalized.trim()];
      if (branch && typeof branch === 'object' && 'next_step' in branch) {
        const idx = steps.findIndex((s: any) => s.step === branch.next_step);
        if (idx !== -1) return idx;
      }
    }
    if (type === 'condition') {
      for (const cond of (step.conditions || [])) {
        if (simMatchCondition(cond, normalized) && cond.next_step !== undefined) {
          const idx = steps.findIndex((s: any) => s.step === cond.next_step);
          if (idx !== -1) return idx;
        }
      }
    }
    return currentIdx + 1;
  };

  const simEvaluateStep = (step: any, normalized: string): string | null => {
    const type = step?.type || 'text';
    if (type === 'choice') {
      const choices = step.choices || {};
      if (normalized.trim() in choices) return null;
      if ('DEFAULT' in choices) return choices['DEFAULT'];
      return null;
    }
    if (type === 'condition') {
      const conds: any[] = step.conditions || [];
      for (const cond of conds) { if (simMatchCondition(cond, normalized)) return null; }
      const def = conds.find((c: any) => c.if === 'default');
      return def ? def.reply : null;
    }
    return null;
  };

  useEffect(() => {
    if (!user) return;
    fetchBotConfig(); fetchScenarios(); fetchKeywords();
    const cid = (user as any)?.company_id;
    if (cid) productsService.getCategories(cid).then(setCategories).catch(() => {});
    // Fetch company ML enabled status and plan
    if (cid) {
      api.get(`/companies/${cid}`).then(res => {
        setCompanyMLEnabled(res.data.ml_enabled || false);
        setCompanyPlan(res.data.subscription_plan || 'FREE');
      }).catch(() => {});
    }
  }, [user]);
  useEffect(() => { simEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [simMessages]);

  const fetchBotConfig = async () => {
    try { const r = await api.get('/bot/config'); setConfig(r.data); }
    catch (e: any) { if (e.response?.status !== 404) setError(e.response?.data?.detail || 'Erreur chargement config'); }
    finally { setLoading(false); }
  };
  const fetchScenarios = async () => {
    try { const r = await api.get('/bot/scenarios'); setScenarios(r.data); } catch {}
  };
  const fetchKeywords = async () => {
    try { const r = await api.get('/bot/keywords'); setKeywords(r.data); } catch {}
  };

  const openNewScenario = () => {
    setEditingScenario(null);
    setScenarioForm({ name: '', trigger_keyword: '', is_active: true });
    setScenarioSteps([{ ...BLANK_STEP }]);
    setShowScenarioModal(true);
  };
  const openEditScenario = (s: BotScenario) => {
    setEditingScenario(s);
    setScenarioForm({ name: s.name, trigger_keyword: s.trigger_keyword, is_active: s.is_active });
    const drafts: StepDraft[] = s.steps.map((st: any) => ({
      type: st.type || 'text',
      message: st.message || st.text || '',
      end_message: st.end_message || '',
      choices: st.choices
        ? Object.entries(st.choices).filter(([k]) => k !== 'DEFAULT').map(([k, v]: any) => ({ key: k, reply: typeof v === 'string' ? v : v.reply || '' }))
        : [{ key: '', reply: '' }],
      conditions: st.conditions || [{ if: 'equals', value: '', reply: '' }],
      catalogue_category: st.catalogue_category || '',
    }));
    setScenarioSteps(drafts.length > 0 ? drafts : [{ ...BLANK_STEP }]);
    setShowScenarioModal(true);
  };
  const openNewKeyword = () => { setEditingKeyword(null); setKeywordForm({ keyword: '', response: '', category: '' }); setShowKeywordModal(true); };
  const openEditKeyword = (k: BotKeyword) => {
    setEditingKeyword(k);
    setKeywordForm({ keyword: k.keyword, response: k.response, category: k.category || '' });
    setShowKeywordModal(true);
  };

  const saveScenario = async (e: React.FormEvent) => {
    e.preventDefault(); setSubmitting(true);
    try {
      const steps = scenarioSteps
        .filter(st => st.type === 'catalogue' || st.message.trim() !== '')
        .map((st, i) => {
          const base: any = { step: i + 1, message: st.message.trim(), type: st.type };
          if (st.end_message.trim()) base.end_message = st.end_message.trim();
          if (st.type === 'choice') {
            const choices: Record<string, string> = {};
            st.choices.forEach(c => { if (c.key.trim()) choices[c.key.trim().toUpperCase()] = c.reply; });
            base.choices = choices;
          }
          if (st.type === 'condition') {
            base.conditions = st.conditions.filter(c => c.value.trim() || c.if === 'default');
          }
          if (st.type === 'catalogue') {
            if (st.catalogue_category) base.catalogue_category = st.catalogue_category;
            base.message = st.catalogue_category
              ? `{catalogue:${st.catalogue_category}}`
              : '{catalogue}';
            if (st.message.trim()) base.message = st.message.trim() + '\n\n' + base.message;
          }
          return base;
        });
      if (steps.length === 0) { setError('Ajoutez au moins une étape.'); setSubmitting(false); return; }
      const payload = { name: scenarioForm.name, trigger_keyword: scenarioForm.trigger_keyword.trim().toUpperCase(), steps, is_active: scenarioForm.is_active };
      if (editingScenario) await api.put(`/bot/scenarios/${editingScenario.id}`, payload);
      else await api.post('/bot/scenarios', payload);
      setShowScenarioModal(false); fetchScenarios();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
    finally { setSubmitting(false); }
  };

  const saveKeyword = async (e: React.FormEvent) => {
    e.preventDefault(); setSubmitting(true);
    try {
      const payload = { keyword: keywordForm.keyword, response: keywordForm.response, category: keywordForm.category || null };
      if (editingKeyword) await api.put(`/bot/keywords/${editingKeyword.id}`, payload);
      else await api.post('/bot/keywords', payload);
      setShowKeywordModal(false); fetchKeywords();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
    finally { setSubmitting(false); }
  };

  const deleteScenario = async (id: string) => {
    if (!confirm('Supprimer ce scénario ?')) return;
    try { await api.delete(`/bot/scenarios/${id}`); fetchScenarios(); } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
  };
  const deleteKeyword = async (id: string) => {
    if (!confirm('Supprimer ce mot-clé ?')) return;
    try { await api.delete(`/bot/keywords/${id}`); fetchKeywords(); } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
  };

  const simulateSend = async () => {
    if (!simInput.trim() || !config) return;
    const userMsg = simInput.trim();
    const normalized = userMsg.trim().toUpperCase();
    setSimMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setSimInput('');

    await new Promise(r => setTimeout(r, 300));

    let botReply: string = simInterpolate(config.unknown_message || 'Je ne comprends pas votre demande.', {});
    let nextState: SimState | null = simState;

    // ── 1. Mid-scenario ────────────────────────────────────────────────────
    if (simState) {
      const sc = scenarios.find(s => s.id === simState.scenarioId);
      const steps = sc?.steps || [];
      const currentStep = steps[simState.currentStep] || {};
      const stepKey = `step_${simState.currentStep + 1}_answer`;
      const newData = { ...simState.collectedData, [stepKey]: userMsg };
      const stepType = currentStep.type || 'text';

      if (stepType === 'catalogue') {
        // Catalogue was already displayed — user is now answering the NEXT step
        const nextIdx = simState.currentStep + 1;
        if (nextIdx >= steps.length) {
          botReply = '✅ Merci !';
          nextState = null;
        } else {
          const nextStep = steps[nextIdx];
          const nextStepData = { ...simState.collectedData, [stepKey]: userMsg };
          botReply = await simResolve(simExtractMsg(nextStep), nextStepData);
          nextState = { ...simState, currentStep: nextIdx, collectedData: nextStepData };
        }
      } else if (stepType === 'handoff') {
        botReply = currentStep.message || 'Un agent va prendre en charge votre demande.';
        nextState = null;
      } else {
        const conditionalReply = simEvaluateStep(currentStep, normalized);
        if (conditionalReply !== null) {
          botReply = await simResolve(conditionalReply, newData);
          nextState = { ...simState, collectedData: newData };
        } else {
          const nextIdx = simNextIndex(currentStep, normalized, simState.currentStep, steps);
          if (nextIdx >= steps.length) {
            // Resolve the choice/condition reply first
            const type = currentStep.type || 'text';
            let resolved: string | undefined;
            if (type === 'choice') resolved = currentStep.choices?.[normalized.trim()] || currentStep.choices?.['DEFAULT'];
            if (type === 'condition') {
              for (const cond of (currentStep.conditions || [])) {
                if (simMatchCondition(cond, normalized)) { resolved = cond.reply; break; }
              }
              if (!resolved) resolved = currentStep.conditions?.find((c: any) => c.if === 'default')?.reply;
            }
            const replyText = resolved ? await simResolve(resolved, newData) : '';
            const endMsg = currentStep.end_message || currentStep.closing;
            const endText = endMsg ? await simResolve(endMsg, newData) : '';
            botReply = [replyText, endText].filter(Boolean).join('\n\n') || '✅ Merci !';
            nextState = null;
          } else {
            // If current step is choice/condition, prepend its reply before the next step message
            const curType = currentStep.type || 'text';
            let choiceReply = '';
            if (curType === 'choice') {
              const cr = currentStep.choices?.[normalized.trim()] || currentStep.choices?.['DEFAULT'];
              if (cr && typeof cr === 'string') choiceReply = await simResolve(cr, newData);
            }
            if (curType === 'condition') {
              for (const cond of (currentStep.conditions || [])) {
                if (simMatchCondition(cond, normalized) && cond.reply) { choiceReply = await simResolve(cond.reply, newData); break; }
              }
            }
            const nextStepObj = steps[nextIdx];
            const nextMsg = await simResolve(simExtractMsg(nextStepObj), newData);
            botReply = [choiceReply, nextMsg].filter(Boolean).join('\n\n');
            // If next step is catalogue, advance past it immediately (no answer needed)
            const nextStepType = (nextStepObj as any).type || 'text';
            const savedIdx = nextStepType === 'catalogue' ? nextIdx + 1 : nextIdx;
            nextState = { scenarioId: simState.scenarioId, currentStep: savedIdx, collectedData: newData };
          }
        }
      }
      setSimState(nextState);
      setSimMessages(prev => [...prev, { role: 'bot', text: botReply }]);
      return;
    }

    // ── 2. Scenario trigger ─────────────────────────────────────────────────
    const matchedSc = scenarios.find(s => s.is_active && normalized === s.trigger_keyword.toUpperCase());
    if (matchedSc && matchedSc.steps.length > 0) {
      const firstStep = matchedSc.steps[0];
      botReply = await simResolve(simExtractMsg(firstStep), {});
      // If first step is catalogue, advance state to next step immediately (catalogue needs no answer)
      const firstStepType = (firstStep as any).type || 'text';
      const initStep = firstStepType === 'catalogue' ? 1 : 0;
      setSimState({ scenarioId: matchedSc.id, currentStep: initStep, collectedData: {} });
      setSimMessages(prev => [...prev, { role: 'bot', text: botReply }]);
      return;
    }

    // ── 3. Keyword match ───────────────────────────────────────────────────
    const matchedKw = keywords.find(k => normalized.includes(k.keyword.toUpperCase()));
    if (matchedKw) botReply = simInterpolate(matchedKw.response, {});

    // ── 4. ML Processing (if enabled and configured) ─────────────────────────
    if (!matchedKw && config.bot_type !== 'NATIVE' && companyMLEnabled && companyPlan !== 'FREE') {
      try {
        const cid = (user as any)?.company_id;
        if (cid) {
          // Use the bot simulate endpoint
          const response = await api.post('/bot/simulate', {
            company_id: cid,
            message: userMsg
          });
          botReply = response.data.response || botReply;
        }
      } catch (e) {
        console.error('ML simulation failed:', e);
        // Fallback to default message
      }
    }

    setSimMessages(prev => [...prev, { role: 'bot', text: botReply }]);
  };

  const startSimulation = () => {
    setSimState(null);
    setSimMessages(config?.welcome_message ? [{ role: 'bot', text: simInterpolate(config.welcome_message, {}) }] : []);
    setActiveTab('simulation');
  };

  if (loading) return <AppLayout><div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div></AppLayout>;

  const TABS: { key: 'config' | 'scenarios' | 'keywords' | 'simulation'; label: string; disabled?: boolean }[] = [
    { key: 'config',     label: '⚙️ Configuration' },
    { key: 'scenarios',  label: `🎭 Scénarios (${scenarios.length})` },
    { key: 'keywords',   label: `🔑 Mots-clés (${keywords.length})` },
    { key: 'simulation', label: '🧪 Simulation', disabled: !config },
  ];

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">🤖 Chatbot</h1>
          <div className="flex gap-2">
            {config && (
              <button onClick={startSimulation}
                className="bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700 text-sm font-medium">
                🧪 Tester le bot
              </button>
            )}
            {!config && (
              <button onClick={() => { setConfigForm({ name: '', welcome_message: 'Bonjour ! Comment puis-je vous aider ?', away_message: '', closing_message: 'Merci, à bientôt !', unknown_message: 'Je ne comprends pas. Souhaitez-vous parler à un agent ?', language: 'fr', timezone: 'Africa/Douala', bot_type: 'NATIVE', followup_timeout_minutes: 60, followup_max_retries: 3, business_hours: null, ml_enabled: false, ml_provider: '', ml_model: '', ml_temperature: '', ml_max_tokens: 500, fallback_strategy: '', confidence_threshold: '' }); setShowConfigModal(true); }}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
                + Créer le bot
              </button>
            )}
          </div>
        </div>

        {error && <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm"><span>{error}</span><button onClick={() => setError('')}>✕</button></div>}

        {!config && (
          <div className="bg-white rounded-xl shadow p-10 text-center text-gray-400">
            <p className="text-5xl mb-3">🤖</p>
            <p className="text-sm">Aucune configuration de bot. Cliquez sur « Créer le bot » pour commencer.</p>
          </div>
        )}

        {config && (
          <>
            <div className="border-b border-gray-200 mb-6">
              <nav className="-mb-px flex space-x-6">
                {TABS.map(t => (
                  <button key={t.key} onClick={() => !t.disabled && setActiveTab(t.key as any)}
                    disabled={t.disabled}
                    className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === t.key ? 'border-green-500 text-green-600' :
                      t.disabled ? 'border-transparent text-gray-300 cursor-not-allowed' :
                      'border-transparent text-gray-500 hover:text-gray-700'
                    }`}>
                    {t.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* ── CONFIG ── */}
            {activeTab === 'config' && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex justify-between items-center mb-5">
                  <h2 className="text-lg font-semibold text-gray-900">Configuration générale</h2>
                  <button onClick={() => { setConfigForm({ name: config.name, welcome_message: config.welcome_message || '', away_message: config.away_message || '', closing_message: config.closing_message || '', unknown_message: config.unknown_message || '', language: config.language, timezone: config.timezone, bot_type: config.bot_type || 'NATIVE', followup_timeout_minutes: (config as any).followup_timeout_minutes ?? 60, followup_max_retries: (config as any).followup_max_retries ?? 3, business_hours: config.business_hours || null, ml_enabled: config.ml_enabled || false, ml_provider: config.ml_provider || '', ml_model: config.ml_model || '', ml_temperature: config.ml_temperature || '', ml_max_tokens: config.ml_max_tokens || 500, fallback_strategy: config.fallback_strategy || '', confidence_threshold: config.confidence_threshold || '' }); setShowConfigModal(true); }}
                    className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 text-sm font-medium">
                    ✏️ Modifier
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {[
                    { label: 'Nom du bot',          value: config.name },
                    { label: 'Type',                value: config.bot_type },
                    { label: 'Langue',              value: config.language },
                    { label: 'Fuseau horaire',      value: config.timezone },
                    { label: 'Message de bienvenue',value: config.welcome_message || '—' },
                    { label: 'Message de clôture',  value: config.closing_message || '—' },
                    { label: 'Message absence',     value: config.away_message || '—' },
                    { label: 'Message inconnu',     value: config.unknown_message || '—' },
                    { label: 'Délai relance (min)',  value: String((config as any).followup_timeout_minutes ?? 60) },
                    { label: 'Nb relances max',      value: String((config as any).followup_max_retries ?? 3) },
                  ].map(f => (
                    <div key={f.label} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">{f.label}</p>
                      <p className="text-sm text-gray-900">{f.value}</p>
                    </div>
                  ))}
                </div>
                {/* Business hours display */}
                {config.business_hours && (
                  <div className="mt-5 bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-500 mb-2">🕐 Horaires d'ouverture</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const).map(day => {
                        const labels: Record<string, string> = { monday: 'Lun', tuesday: 'Mar', wednesday: 'Mer', thursday: 'Jeu', friday: 'Ven', saturday: 'Sam', sunday: 'Dim' };
                        const dayConf = config.business_hours?.[day];
                        return (
                          <div key={day} className={`text-xs rounded px-2 py-1.5 ${dayConf ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-400'}`}>
                            <span className="font-medium">{labels[day]}</span>{' '}
                            {dayConf ? `${dayConf.open}–${dayConf.close}` : 'Fermé'}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── SCENARIOS ── */}
            {activeTab === 'scenarios' && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex justify-between items-center mb-5">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Scénarios</h2>
                    <p className="text-xs text-gray-400 mt-0.5">Un scénario se déclenche quand le client envoie le mot-clé déclencheur.</p>
                  </div>
                  <button onClick={openNewScenario} className="bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 text-sm font-medium">+ Nouveau</button>
                </div>
                <div className="space-y-3">
                  {scenarios.length === 0 && <p className="text-center text-gray-400 py-8 text-sm">Aucun scénario. Créez-en un pour commencer.</p>}
                  {scenarios.map(s => (
                    <div key={s.id} className="border border-gray-200 rounded-lg p-4 flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-gray-900">{s.name}</span>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                            {s.is_active ? 'Actif' : 'Inactif'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap mt-0.5">
                          <p className="text-xs text-gray-500">Déclencheur : <span className="font-mono bg-gray-100 px-1 rounded">{s.trigger_keyword}</span></p>
                          <span className="text-xs text-indigo-600 font-medium">{s.steps.length} étape{s.steps.length > 1 ? 's' : ''}</span>
                        </div>
                        <div className="mt-1.5 space-y-0.5">
                          {s.steps.slice(0, 2).map((st: any, i: number) => (
                            <p key={i} className="text-xs text-gray-500 truncate">
                              <span className="text-gray-400 font-medium">{i + 1}.</span> {st.message || st.text || st.response || ''}
                            </p>
                          ))}
                          {s.steps.length > 2 && <p className="text-xs text-gray-400">+{s.steps.length - 2} autre{s.steps.length - 2 > 1 ? 's' : ''}...</p>}
                        </div>
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        <button onClick={() => openEditScenario(s)} className="text-indigo-600 hover:text-indigo-800 text-xs font-medium">Modifier</button>
                        <button onClick={() => deleteScenario(s.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Supprimer</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── KEYWORDS ── */}
            {activeTab === 'keywords' && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex justify-between items-center mb-5">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Mots-clés</h2>
                    <p className="text-xs text-gray-400 mt-0.5">Réponse instantanée quand le client mentionne le mot-clé.</p>
                  </div>
                  <button onClick={openNewKeyword} className="bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 text-sm font-medium">+ Nouveau</button>
                </div>
                {keywords.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {[...new Set(keywords.map(k => k.category).filter(Boolean))].map(cat => (
                      <span key={cat} className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">{cat}</span>
                    ))}
                  </div>
                )}
                <div className="space-y-3">
                  {keywords.length === 0 && <p className="text-center text-gray-400 py-8 text-sm">Aucun mot-clé. Ajoutez-en un pour que le bot réponde automatiquement.</p>}
                  {keywords.map(k => (
                    <div key={k.id} className="border border-gray-200 rounded-lg p-4 flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-sm font-semibold text-gray-900 bg-gray-100 px-2 py-0.5 rounded">{k.keyword}</span>
                          {k.category && <span className="text-xs text-amber-600 font-medium">{k.category}</span>}
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-2">{k.response}</p>
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        <button onClick={() => openEditKeyword(k)} className="text-indigo-600 hover:text-indigo-800 text-xs font-medium">Modifier</button>
                        <button onClick={() => deleteKeyword(k.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Supprimer</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── SIMULATION ── */}
            {activeTab === 'simulation' && (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col" style={{ height: '520px' }}>
                <div className="bg-green-600 px-4 py-3 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white font-bold text-sm">🤖</div>
                  <div>
                    <p className="text-white font-semibold text-sm">{config.name}</p>
                    <p className="text-green-100 text-xs">Simulation locale — test hors WhatsApp</p>
                  </div>
                  <button onClick={() => { setSimState(null); setSimMessages(config?.welcome_message ? [{ role: 'bot', text: simInterpolate(config.welcome_message, {}) }] : []); }}
                    className="ml-auto text-green-100 hover:text-white text-xs">↺ Recommencer</button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
                  {simMessages.length === 0 && (
                    <p className="text-center text-gray-400 text-sm mt-8">Envoyez un message pour tester le bot.</p>
                  )}
                  {simMessages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-xs px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap break-words ${
                        m.role === 'user'
                          ? 'bg-green-600 text-white rounded-br-sm'
                          : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm'
                      }`}>
                        {m.text.split('\n').map((line, li) => {
                          const formatted = line
                            .replace(/\*([^*]+)\*/g, '<strong>$1</strong>')
                            .replace(/_([^_]+)_/g, '<em>$1</em>');
                          return <span key={li} dangerouslySetInnerHTML={{ __html: formatted || '&nbsp;' }} className="block" />;
                        })}
                      </div>
                    </div>
                  ))}
                  <div ref={simEndRef} />
                </div>

                <div className="border-t border-gray-200 p-3 flex gap-2 bg-white">
                  <input
                    value={simInput}
                    onChange={e => setSimInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && simulateSend()}
                    placeholder="Tapez un message..."
                    className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <button onClick={simulateSend}
                    className="bg-green-600 text-white px-4 py-2 rounded-full hover:bg-green-700 text-sm font-medium">
                    Envoyer
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Modal Config ── */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="font-bold text-gray-900 mb-4">{config ? '✏️ Modifier le bot' : '🤖 Créer le bot'}</h3>
            <form onSubmit={async e => { e.preventDefault(); setSubmitting(true); try { 
              const formData = { ...configForm };
              // Auto-set ml_enabled based on bot_type
              if (formData.bot_type === 'ML' || formData.bot_type === 'HYBRID') {
                formData.ml_enabled = true;
              } else {
                formData.ml_enabled = false;
              }
              if (config) await api.put('/bot/config', formData); else await api.post('/bot/config', formData); 
              setShowConfigModal(false); fetchBotConfig(); } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); } finally { setSubmitting(false); } }} className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Nom du bot *</label>
                <input required value={configForm.name} onChange={e => setConfigForm({...configForm, name: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Mon chatbot" /></div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mode du bot</label>
                {companyPlan === 'FREE' ? (
                  <div className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200">
                    Mode Natif (règles, scénarios, mots-clés)
                    <p className="text-xs text-gray-500 mt-1">Le ML n'est pas disponible avec le plan FREE. Contactez le Super Admin pour passer à un plan supérieur.</p>
                  </div>
                ) : (
                  <select 
                    value={configForm.bot_type || 'NATIVE'}
                    onChange={e => setConfigForm({...configForm, bot_type: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500"
                  >
                    <option value="NATIVE">Mode Natif (règles, scénarios, mots-clés)</option>
                    <option value="ML">Mode ML (Machine Learning uniquement)</option>
                    <option value="HYBRID">Mode Hybride (ML + fallback natif)</option>
                  </select>
                )}
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Message de bienvenue</label>
                <textarea value={configForm.welcome_message} onChange={e => setConfigForm({...configForm, welcome_message: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" rows={2} placeholder="Bonjour ! Comment puis-je vous aider ?" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Message de clôture</label>
                <textarea value={configForm.closing_message} onChange={e => setConfigForm({...configForm, closing_message: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" rows={2} placeholder="Merci, à bientôt !" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Message absence</label>
                <textarea value={configForm.away_message} onChange={e => setConfigForm({...configForm, away_message: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" rows={2} placeholder="Nous sommes absents pour le moment..." /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Message inconnu</label>
                <textarea value={configForm.unknown_message} onChange={e => setConfigForm({...configForm, unknown_message: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" rows={2} placeholder="Je ne comprends pas. Souhaitez-vous parler à un agent ?" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Langue</label>
                  <input value={configForm.language} onChange={e => setConfigForm({...configForm, language: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="fr" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Fuseau horaire</label>
                  <select value={configForm.timezone} onChange={e => setConfigForm({...configForm, timezone: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500">
                    <option value="" disabled>Choisir un fuseau horaire</option>
                    {TIMEZONES.map(tz => (
                      <option key={tz.value} value={tz.value}>{tz.label}</option>
                    ))}
                  </select></div>
              </div>
              <div className="border-t pt-3 mt-1">
                <p className="text-xs font-semibold text-gray-500 mb-2">🕐 Horaires d'ouverture <span className="font-normal text-gray-400">(le bot envoie le message d'absence hors de ces horaires)</span></p>
                <div className="space-y-1.5">
                  {(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const).map(day => {
                    const labels: Record<string, string> = { monday: 'Lundi', tuesday: 'Mardi', wednesday: 'Mercredi', thursday: 'Jeudi', friday: 'Vendredi', saturday: 'Samedi', sunday: 'Dimanche' };
                    const bh = configForm.business_hours || {};
                    const dayConf = bh[day];
                    const isOpen = !!dayConf;
                    return (
                      <div key={day} className="flex items-center gap-2">
                        <label className="w-20 text-xs font-medium text-gray-700">{labels[day]}</label>
                        <input type="checkbox" checked={isOpen} onChange={e => {
                          const newBh = { ...bh };
                          if (e.target.checked) newBh[day] = { open: '07:00', close: '17:00' };
                          else newBh[day] = null;
                          setConfigForm({ ...configForm, business_hours: newBh });
                        }} className="rounded border-gray-300 text-green-600 focus:ring-green-500" />
                        {isOpen && (
                          <>
                            <input type="time" value={dayConf?.open || '07:00'} onChange={e => {
                              const newBh = { ...bh };
                              newBh[day] = { open: e.target.value, close: dayConf?.close || '17:00' };
                              setConfigForm({ ...configForm, business_hours: newBh });
                            }} className="border border-gray-300 rounded px-2 py-1 text-xs" />
                            <span className="text-xs text-gray-400">à</span>
                            <input type="time" value={dayConf?.close || '17:00'} onChange={e => {
                              const newBh = { ...bh };
                              newBh[day] = { open: dayConf?.open || '07:00', close: e.target.value };
                              setConfigForm({ ...configForm, business_hours: newBh });
                            }} className="border border-gray-300 rounded px-2 py-1 text-xs" />
                          </>
                        )}
                        {!isOpen && <span className="text-xs text-red-400 italic">Fermé</span>}
                      </div>
                    );
                  })}
                </div>
                <p className="text-xs text-gray-400 mt-2">💡 Si aucun jour n'est coché, le bot est actif 24h/24.</p>
              </div>
              <div className="border-t pt-3 mt-1">
                <p className="text-xs font-semibold text-gray-500 mb-2">⏱ Relance automatique (inactivité scénario)</p>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="block text-sm font-medium text-gray-700 mb-1">Délai avant relance <span className="text-gray-400">(minutes)</span></label>
                    <input type="number" min={1} value={configForm.followup_timeout_minutes} onChange={e => setConfigForm({...configForm, followup_timeout_minutes: parseInt(e.target.value) || 60})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" /></div>
                  <div><label className="block text-sm font-medium text-gray-700 mb-1">Nb max de relances</label>
                    <input type="number" min={1} max={10} value={configForm.followup_max_retries} onChange={e => setConfigForm({...configForm, followup_max_retries: parseInt(e.target.value) || 3})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" /></div>
                </div>
                <p className="text-xs text-gray-400 mt-1">Après <strong>{configForm.followup_max_retries}</strong> relances sans réponse la conversation est automatiquement clôturée.</p>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowConfigModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">{submitting ? '...' : 'Enregistrer'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal Scénario ── */}
      {showScenarioModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl shadow-xl max-h-[92vh] overflow-y-auto">
            <h3 className="font-bold text-gray-900 mb-4">{editingScenario ? '✏️ Modifier le scénario' : '+ Nouveau scénario'}</h3>
            <form onSubmit={saveScenario} className="space-y-4">

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom du scénario *</label>
                  <input required value={scenarioForm.name} onChange={e => setScenarioForm({...scenarioForm, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Ex: Commande produit" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mot-clé déclencheur *</label>
                  <input required value={scenarioForm.trigger_keyword} onChange={e => setScenarioForm({...scenarioForm, trigger_keyword: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500 uppercase" placeholder="Ex: COMMANDER" />
                </div>
              </div>

              {/* Steps builder */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">Étapes du scénario *</label>
                  <span className="text-xs text-gray-400">{scenarioSteps.length} étape{scenarioSteps.length > 1 ? 's' : ''}</span>
                </div>
                <div className="space-y-3">
                  {scenarioSteps.map((step, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center flex-shrink-0">{idx + 1}</div>
                        <select
                          value={step.type}
                          onChange={e => {
                            const updated = [...scenarioSteps];
                            updated[idx] = { ...updated[idx], type: e.target.value as StepType };
                            setScenarioSteps(updated);
                          }}
                          className="border border-gray-300 rounded-lg px-2 py-1 text-xs bg-white focus:ring-2 focus:ring-green-500">
                          <option value="text">📝 Texte (linéaire)</option>
                          <option value="choice">🔢 Choix (1, 2, 3...)</option>
                          <option value="condition">🔀 Condition (si/sinon)</option>
                          <option value="handoff">📞 Transfert agent</option>
                          <option value="catalogue">🛍️ Catalogue produits</option>
                        </select>
                        {scenarioSteps.length > 1 && (
                          <button type="button" onClick={() => setScenarioSteps(scenarioSteps.filter((_, i) => i !== idx))}
                            className="ml-auto text-red-400 hover:text-red-600 text-sm">✕ Supprimer</button>
                        )}
                      </div>

                      {step.type === 'catalogue' ? (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-2">
                          <p className="text-xs font-semibold text-green-700">🛍️ Affichage du catalogue produits</p>
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <label className="block text-xs text-gray-600 mb-1">Filtrer par catégorie <span className="text-gray-400">(optionnel)</span></label>
                              <select
                                value={step.catalogue_category}
                                onChange={e => { const u = [...scenarioSteps]; u[idx] = { ...u[idx], catalogue_category: e.target.value }; setScenarioSteps(u); }}
                                className="w-full border border-green-300 rounded-lg px-2 py-1.5 text-xs bg-white focus:ring-1 focus:ring-green-500">
                                <option value="">Tous les produits</option>
                                {categories.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                              </select>
                            </div>
                            <div>
                              <label className="block text-xs text-gray-600 mb-1">Message avant la liste <span className="text-gray-400">(optionnel)</span></label>
                              <input
                                value={step.message}
                                onChange={e => { const u = [...scenarioSteps]; u[idx] = { ...u[idx], message: e.target.value }; setScenarioSteps(u); }}
                                className="w-full border border-green-300 rounded-lg px-2 py-1.5 text-xs focus:ring-1 focus:ring-green-500 bg-white"
                                placeholder="Ex: Voici nos articles disponibles :" />
                            </div>
                          </div>
                          <p className="text-xs text-green-600">Le bot enverra la liste des produits{step.catalogue_category ? ` de la catégorie <strong>${step.catalogue_category}</strong>` : ''} automatiquement.</p>
                          <p className="text-xs text-gray-500 mt-1">💡 Vous pouvez aussi utiliser <span className="font-mono bg-white px-1 rounded border">{'{catalogue}'}</span> ou <span className="font-mono bg-white px-1 rounded border">{`{catalogue:${step.catalogue_category || 'NomCat'}}`}</span> dans n'importe quel message.</p>
                        </div>
                      ) : step.type === 'handoff' ? (
                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 space-y-2">
                          <p className="text-xs font-semibold text-amber-700">📞 Message envoyé au client avant transfert :</p>
                          <textarea
                            value={step.message}
                            onChange={e => { const u = [...scenarioSteps]; u[idx] = { ...u[idx], message: e.target.value }; setScenarioSteps(u); }}
                            rows={2}
                            className="w-full border border-amber-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 resize-none bg-white"
                            placeholder="Ex: Merci, un agent va vous contacter dans quelques instants. Merci de patienter."
                          />
                          <p className="text-xs text-amber-600">⚠️ Ce step termine le scénario et passe la conversation en statut <strong>WAITING</strong> — les agents verront une alerte.</p>
                        </div>
                      ) : (
                        <textarea
                          value={step.message}
                          onChange={e => { const u = [...scenarioSteps]; u[idx] = { ...u[idx], message: e.target.value }; setScenarioSteps(u); }}
                          rows={2}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 resize-none bg-white"
                          placeholder={step.type === 'choice' ? 'Message affiché avec les choix (ex: Quel produit ?\n1 - Laptop\n2 - Souris)' : step.type === 'condition' ? 'Question posée au client (ex: Confirmez-vous ? oui/non)' : `Message de l'étape ${idx + 1}...`}
                        />
                      )}
                      {step.type !== 'catalogue' && step.type !== 'handoff' && (
                        <p className="text-xs text-indigo-500 mt-1 flex flex-wrap gap-1 items-center">
                          <span className="text-gray-400">Variables :</span>
                          {idx > 0 && Array.from({length: idx}, (_, i) => <span key={i} className="font-mono bg-indigo-50 px-1 rounded">{`{step_${i + 1}_answer}`}</span>)}
                          <span className="font-mono bg-indigo-50 px-1 rounded">{'{now}'}</span>
                          <span className="font-mono bg-indigo-50 px-1 rounded">{'{date}'}</span>
                          <span className="font-mono bg-indigo-50 px-1 rounded">{'{time}'}</span>
                          <span className="font-mono bg-green-50 text-green-700 px-1 rounded">{'{catalogue}'}</span>
                          {categories.map(c => (
                            <span key={c.id} className="font-mono bg-green-50 text-green-700 px-1 rounded">{`{catalogue:${c.name}}`}</span>
                          ))}
                          <span className="font-mono bg-green-50 text-green-700 px-1 rounded">{'{produit:NomProduit}'}</span>
                        </p>
                      )}

                      {/* CHOICE options */}
                      {step.type === 'choice' && (
                        <div className="mt-2 space-y-1.5">
                          <p className="text-xs font-medium text-gray-600">Réponses possibles :</p>
                          {step.choices.map((c, ci) => (
                            <div key={ci} className="flex gap-2 items-center">
                              <input
                                value={c.key}
                                onChange={e => { const u = [...scenarioSteps]; u[idx].choices[ci] = { ...c, key: e.target.value }; setScenarioSteps(u); }}
                                className="w-16 border border-gray-300 rounded px-2 py-1 text-xs font-mono focus:ring-1 focus:ring-green-500 uppercase"
                                placeholder="1"
                              />
                              <span className="text-gray-400 text-xs">→</span>
                              <input
                                value={c.reply}
                                onChange={e => { const u = [...scenarioSteps]; u[idx].choices[ci] = { ...c, reply: e.target.value }; setScenarioSteps(u); }}
                                className="flex-1 border border-gray-300 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-green-500"
                                placeholder="Réponse ou confirmation..."
                              />
                              {step.choices.length > 1 && (
                                <button type="button" onClick={() => { const u = [...scenarioSteps]; u[idx].choices = u[idx].choices.filter((_, i) => i !== ci); setScenarioSteps(u); }}
                                  className="text-red-400 hover:text-red-600 text-xs">✕</button>
                              )}
                            </div>
                          ))}
                          <button type="button"
                            onClick={() => { const u = [...scenarioSteps]; u[idx].choices = [...u[idx].choices, { key: '', reply: '' }]; setScenarioSteps(u); }}
                            className="text-xs text-green-600 hover:text-green-800">+ Ajouter un choix</button>
                          <p className="text-xs text-gray-400">Astuce : ajoutez un choix avec la clé <span className="font-mono bg-gray-100 px-1 rounded">DEFAULT</span> pour les réponses invalides (re-demande).</p>
                        </div>
                      )}

                      {/* CONDITION rules */}
                      {step.type === 'condition' && (
                        <div className="mt-2 space-y-1.5">
                          <p className="text-xs font-medium text-gray-600">Conditions :</p>
                          {step.conditions.map((c, ci) => (
                            <div key={ci} className="flex gap-2 items-center flex-wrap">
                              <select
                                value={c.if}
                                onChange={e => { const u = [...scenarioSteps]; u[idx].conditions[ci] = { ...c, if: e.target.value as any }; setScenarioSteps(u); }}
                                className="border border-gray-300 rounded px-2 py-1 text-xs bg-white">
                                <option value="equals">= égal à</option>
                                <option value="contains">⊃ contient</option>
                                <option value="starts_with">↗ commence par</option>
                                <option value="not_equals">≠ différent de</option>
                                <option value="default">★ sinon (défaut)</option>
                              </select>
                              {c.if !== 'default' && (
                                <input
                                  value={c.value}
                                  onChange={e => { const u = [...scenarioSteps]; u[idx].conditions[ci] = { ...c, value: e.target.value }; setScenarioSteps(u); }}
                                  className="w-24 border border-gray-300 rounded px-2 py-1 text-xs font-mono focus:ring-1 focus:ring-green-500"
                                  placeholder="OUI"
                                />
                              )}
                              <span className="text-gray-400 text-xs">→</span>
                              <input
                                value={c.reply}
                                onChange={e => { const u = [...scenarioSteps]; u[idx].conditions[ci] = { ...c, reply: e.target.value }; setScenarioSteps(u); }}
                                className="flex-1 min-w-32 border border-gray-300 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-green-500"
                                placeholder="Réponse..."
                              />
                              {step.conditions.length > 1 && (
                                <button type="button" onClick={() => { const u = [...scenarioSteps]; u[idx].conditions = u[idx].conditions.filter((_, i) => i !== ci); setScenarioSteps(u); }}
                                  className="text-red-400 hover:text-red-600 text-xs">✕</button>
                              )}
                            </div>
                          ))}
                          <button type="button"
                            onClick={() => { const u = [...scenarioSteps]; u[idx].conditions = [...u[idx].conditions, { if: 'equals', value: '', reply: '' }]; setScenarioSteps(u); }}
                            className="text-xs text-green-600 hover:text-green-800">+ Ajouter une condition</button>
                        </div>
                      )}

                      <div className="mt-2">
                        <input
                          value={step.end_message}
                          onChange={e => { const u = [...scenarioSteps]; u[idx] = { ...u[idx], end_message: e.target.value }; setScenarioSteps(u); }}
                          className="w-full border border-dashed border-gray-300 rounded-lg px-3 py-1.5 text-xs text-gray-500 focus:ring-1 focus:ring-green-400 bg-white"
                          placeholder="Message de clôture optionnel (affiché si c'est la dernière étape)"
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <button type="button"
                  onClick={() => setScenarioSteps([...scenarioSteps, { ...BLANK_STEP }])}
                  className="mt-2 text-sm text-green-600 hover:text-green-800 font-medium flex items-center gap-1">
                  + Ajouter une étape
                </button>
              </div>

              <div className="flex items-center gap-2">
                <input type="checkbox" id="sc_active" checked={scenarioForm.is_active} onChange={e => setScenarioForm({...scenarioForm, is_active: e.target.checked})} className="rounded" />
                <label htmlFor="sc_active" className="text-sm text-gray-700">Actif</label>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowScenarioModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">{submitting ? '...' : editingScenario ? 'Enregistrer' : 'Créer'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal Mot-clé ── */}
      {showKeywordModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">{editingKeyword ? '✏️ Modifier le mot-clé' : '+ Nouveau mot-clé'}</h3>
            <form onSubmit={saveKeyword} className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Mot-clé *</label>
                <input required value={keywordForm.keyword} onChange={e => setKeywordForm({...keywordForm, keyword: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Ex: horaires, prix, aide..." />
                <p className="text-xs text-gray-400 mt-1">Insensible à la casse. Peut être un mot ou une courte phrase.</p></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Réponse *</label>
                <textarea required value={keywordForm.response} onChange={e => setKeywordForm({...keywordForm, response: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" rows={4} placeholder="Réponse automatique envoyée au client..." /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Catégorie <span className="text-gray-400">(optionnel)</span></label>
                <input value={keywordForm.category} onChange={e => setKeywordForm({...keywordForm, category: e.target.value})} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Ex: FAQ, Support, Ventes..." /></div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowKeywordModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">{submitting ? '...' : editingKeyword ? 'Enregistrer' : 'Créer'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
