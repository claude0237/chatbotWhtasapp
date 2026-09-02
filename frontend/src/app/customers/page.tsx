'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface CustomerExtra {
  email?: string;
  company_name?: string;
  city?: string;
  country?: string;
  language?: string;
  notes?: string;
  source?: string;
  tags?: string[];
  [key: string]: unknown;
}
interface Customer {
  id: string;
  company_id: string;
  phone_number: string;
  name: string | null;
  profile_picture_url: string | null;
  extra_data: CustomerExtra | null;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}
interface ConvSummary {
  id: string;
  status: string;
  priority: string;
  assigned_agent_id: string | null;
  last_activity_at: string;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  OPEN: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300', WAITING: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300',
  AI: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300', AGENT: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
  CLOSED: 'bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400', ARCHIVED: 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400',
};

const SOURCE_OPTIONS = ['WhatsApp', 'Formulaire', 'Référence', 'Publicité', 'Autre'];
const LANG_OPTIONS = ['Français', 'English', 'Arabe', 'Espagnol', 'Autre'];

function Avatar({ name, phone, size = 'md' }: { name?: string | null; phone: string; size?: 'sm' | 'md' | 'lg' }) {
  const letter = (name || phone)[0]?.toUpperCase() || '?';
  const sz = size === 'lg' ? 'w-16 h-16 text-2xl' : size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm';
  return (
    <div className={`${sz} rounded-full bg-green-100 dark:bg-green-900/40 flex items-center justify-center flex-shrink-0 text-green-700 dark:text-green-300 font-bold`}>
      {letter}
    </div>
  );
}

const emptyForm = {
  name: '', email: '', company_name: '', city: '', country: '',
  language: '', notes: '', source: '', profile_picture_url: '',
  tags: '' as string,
};

export default function CustomersPage() {
  const { user } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [totalCustomers, setTotalCustomers] = useState(0);
  const [selected, setSelectedRaw] = useState<Customer | null>(null);
  const pendingCustomerHash = useRef<string | null>(typeof window !== 'undefined' ? window.location.hash.replace('#', '') || null : null);
  const [conversations, setConversations] = useState<ConvSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [convLoading, setConvLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [search, setSearch] = useState('');
  const [form, setForm] = useState(emptyForm);

  const setSelected = useCallback((c: Customer | null) => {
    setSelectedRaw(c);
    if (typeof window !== 'undefined') {
      window.history.replaceState(null, '', c ? `#${c.id}` : '#');
    }
  }, []);

  const fetchCustomers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/customers/', { params: { limit: 500 } });
      const data = res.data;
      const list: Customer[] = Array.isArray(data) ? data : (data.customers || []);
      setCustomers(list);
      setTotalCustomers(data.total ?? (Array.isArray(data) ? data.length : 0));
      // Restore selected customer from URL hash on initial load
      if (pendingCustomerHash.current) {
        const restored = list.find(c => c.id === pendingCustomerHash.current);
        if (restored) setSelected(restored);
        pendingCustomerHash.current = null;
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur chargement');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (user) fetchCustomers(); }, [user]);

  const fetchConversations = useCallback(async (id: string) => {
    setConvLoading(true);
    try {
      const res = await api.get(`/customers/${id}/conversations`);
      setConversations(res.data);
    } catch { setConversations([]); }
    finally { setConvLoading(false); }
  }, []);

  const openCustomer = (c: Customer) => {
    setSelected(c);
    setEditing(false);
    setSuccess('');
    setError('');
    fetchConversations(c.id);
    const ex = c.extra_data || {};
    setForm({
      name: c.name || '',
      email: ex.email || '',
      company_name: ex.company_name || '',
      city: ex.city || '',
      country: ex.country || '',
      language: ex.language || '',
      notes: ex.notes || '',
      source: ex.source || '',
      profile_picture_url: c.profile_picture_url || '',
      tags: (ex.tags || []).join(', '),
    });
  };

  const handleDeleteCustomer = async () => {
    if (!selected) return;
    if (!confirm(`Supprimer le contact ${selected.name || selected.phone_number} et toutes ses conversations ? Cette action est irréversible.`)) return;
    try {
      await api.delete(`/customers/${selected.id}`);
      setSelected(null);
      setConversations([]);
      fetchCustomers();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur suppression contact'); }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    setSubmitting(true);
    try {
      const tagsArr = form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
      const payload = {
        name: form.name || undefined,
        profile_picture_url: form.profile_picture_url || undefined,
        email: form.email || undefined,
        company_name: form.company_name || undefined,
        city: form.city || undefined,
        country: form.country || undefined,
        language: form.language || undefined,
        notes: form.notes || undefined,
        source: form.source || undefined,
        tags: tagsArr.length ? tagsArr : undefined,
      };
      const res = await api.put(`/customers/${selected.id}`, payload);
      setSelected(res.data);
      setEditing(false);
      setSuccess('Fiche mise à jour.');
      setCustomers(prev => prev.map(c => c.id === res.data.id ? res.data : c));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur mise à jour');
    } finally { setSubmitting(false); }
  };

  const f = (v: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [v]: e.target.value }));

  const filtered = customers.filter(c =>
    !search ||
    (c.name || '').toLowerCase().includes(search.toLowerCase()) ||
    c.phone_number.includes(search) ||
    (c.extra_data?.email || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      <div className="flex flex-col h-full" style={{ height: 'calc(100vh - 112px)' }}>

        {/* Header */}
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">👤 Carnet de contacts</h1>
            <p className="text-xs text-gray-400 mt-0.5">{totalCustomers} contact(s) WhatsApp</p>
          </div>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="🔍 Nom, téléphone, email…"
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 text-sm w-64 focus:ring-2 focus:ring-green-500"
          />
        </div>

        {error && <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-2 rounded-lg mb-3 flex justify-between text-sm flex-shrink-0"><span>{error}</span><button onClick={() => setError('')}>✕</button></div>}
        {success && <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 px-4 py-2 rounded-lg mb-3 flex justify-between text-sm flex-shrink-0"><span>✅ {success}</span><button onClick={() => setSuccess('')}>✕</button></div>}

        <div className="flex gap-4 flex-1 min-h-0">

          {/* ── Liste contacts ── */}
          <div className="w-64 flex-shrink-0 bg-white dark:bg-gray-800 rounded-xl shadow flex flex-col overflow-hidden">
            <div className="px-3 py-2.5 bg-gray-50 dark:bg-gray-800 border-b text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
              {filtered.length} contact{filtered.length !== 1 ? 's' : ''}
            </div>
            <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
              {loading ? (
                <div className="p-8 text-center text-gray-400 text-sm">Chargement…</div>
              ) : filtered.length === 0 ? (
                <div className="p-8 text-center text-gray-400 text-sm">Aucun contact</div>
              ) : filtered.map(c => (
                <div key={c.id} onClick={() => openCustomer(c)}
                  className={`px-3 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${selected?.id === c.id ? 'bg-green-50 dark:bg-green-900/30 border-l-4 border-green-500' : 'border-l-4 border-transparent'}`}>
                  <div className="flex items-center gap-2.5">
                    <Avatar name={c.name} phone={c.phone_number} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{c.name || <span className="text-gray-400 italic">Inconnu</span>}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{c.phone_number}</p>
                      {c.extra_data?.email && <p className="text-xs text-gray-400 truncate">{c.extra_data.email}</p>}
                    </div>
                  </div>
                  {c.extra_data?.tags && (c.extra_data.tags as string[]).length > 0 && (
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {(c.extra_data.tags as string[]).slice(0, 2).map((t, i) => (
                        <span key={i} className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* ── Fiche détail ── */}
          <div className="flex-1 min-w-0 flex flex-col gap-4 overflow-y-auto">
            {selected ? (
              <>
                {/* Carte profil */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                  <div className="flex items-start justify-between gap-4 mb-5">
                    <div className="flex items-center gap-4">
                      <Avatar name={selected.name} phone={selected.phone_number} size="lg" />
                      <div>
                        <h2 className="text-lg font-bold text-gray-900 dark:text-white">{selected.name || <span className="text-gray-400 italic">Nom inconnu</span>}</h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">📱 {selected.phone_number}</p>
                        {selected.extra_data?.email && <p className="text-sm text-gray-500 dark:text-gray-400">✉️ {selected.extra_data.email}</p>}
                        {selected.extra_data?.company_name && <p className="text-sm text-gray-500 dark:text-gray-400">🏢 {selected.extra_data.company_name}</p>}
                      </div>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      {!editing ? (
                        <>
                          <button onClick={() => setEditing(true)}
                            className="bg-indigo-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-indigo-700 font-medium">
                            ✏️ Modifier
                          </button>
                          <button onClick={handleDeleteCustomer}
                            className="bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 px-4 py-1.5 rounded-lg text-sm hover:bg-red-200 dark:hover:bg-red-800 font-medium"
                            title="Supprimer le contact">
                            🗑️ Supprimer
                          </button>
                        </>
                      ) : (
                        <button onClick={() => setEditing(false)}
                          className="border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 px-4 py-1.5 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
                          Annuler
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Tags */}
                  {!editing && selected.extra_data?.tags && (selected.extra_data.tags as string[]).length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {(selected.extra_data.tags as string[]).map((t, i) => (
                        <span key={i} className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-900 px-2 py-0.5 rounded-full font-medium">{t}</span>
                      ))}
                    </div>
                  )}

                  {/* Infos auto */}
                  {!editing && (
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        ['📅 Première vue', new Date(selected.first_seen_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })],
                        ['🕐 Dernière activité', new Date(selected.last_seen_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })],
                        ['📌 Source', selected.extra_data?.source || '—'],
                        ['🌍 Ville', selected.extra_data?.city || '—'],
                        ['🗺️ Pays', selected.extra_data?.country || '—'],
                        ['🗣️ Langue', selected.extra_data?.language || '—'],
                      ].map(([label, value]) => (
                        <div key={label} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                          <p className="text-xs text-gray-400 mb-0.5">{label}</p>
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-100">{value}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Notes affichage */}
                  {!editing && selected.extra_data?.notes && (
                    <div className="mt-3 bg-amber-50 dark:bg-amber-900/30 border border-amber-100 dark:border-amber-900 rounded-lg p-3">
                      <p className="text-xs text-amber-600 dark:text-amber-400 font-medium mb-1">📝 Notes internes</p>
                      <p className="text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap">{selected.extra_data.notes}</p>
                    </div>
                  )}

                  {/* Formulaire d'édition */}
                  {editing && (
                    <form onSubmit={handleSave} className="space-y-4">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Nom complet</label>
                          <input value={form.name} onChange={f('name')} placeholder="Jean Dupont"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Email</label>
                          <input type="email" value={form.email} onChange={f('email')} placeholder="jean@exemple.com"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Entreprise</label>
                          <input value={form.company_name} onChange={f('company_name')} placeholder="ACME Corp"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Ville</label>
                          <input value={form.city} onChange={f('city')} placeholder="Paris"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Pays</label>
                          <input value={form.country} onChange={f('country')} placeholder="France"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Langue</label>
                          <select value={form.language} onChange={f('language')}
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500">
                            <option value="">— Sélectionner —</option>
                            {LANG_OPTIONS.map(l => <option key={l} value={l}>{l}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Source d'acquisition</label>
                          <select value={form.source} onChange={f('source')}
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500">
                            <option value="">— Sélectionner —</option>
                            {SOURCE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Tags (séparés par virgule)</label>
                          <input value={form.tags} onChange={f('tags')} placeholder="vip, prospect, support"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div className="col-span-2">
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Photo (URL)</label>
                          <input type="url" value={form.profile_picture_url} onChange={f('profile_picture_url')} placeholder="https://…"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
                        </div>
                        <div className="col-span-2">
                          <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">Notes internes</label>
                          <textarea value={form.notes} onChange={f('notes')} rows={3}
                            placeholder="Notes privées sur ce client…"
                            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 resize-none" />
                        </div>
                      </div>
                      <div className="flex gap-3 pt-2">
                        <button type="button" onClick={() => setEditing(false)}
                          className="flex-1 border border-gray-300 dark:border-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700">Annuler</button>
                        <button type="submit" disabled={submitting}
                          className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 font-semibold">
                          {submitting ? 'Enregistrement…' : '💾 Enregistrer'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>

                {/* Historique conversations */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900 dark:text-white text-sm">💬 Historique des conversations</h3>
                    <Link href={`/conversations`}
                      className="text-xs text-green-600 dark:text-green-400 hover:underline">Voir toutes →</Link>
                  </div>
                  {convLoading ? (
                    <p className="text-sm text-gray-400 text-center py-4">Chargement…</p>
                  ) : conversations.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-4">Aucune conversation</p>
                  ) : (
                    <div className="space-y-2">
                      {conversations.map(c => (
                        <div key={c.id} className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLORS[c.status] || 'bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400'}`}>
                              {c.status}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {new Date(c.last_activity_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}
                            </span>
                          </div>
                          <span className="text-xs text-gray-400">{c.priority}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow flex flex-col items-center justify-center text-gray-400 min-h-64">
                <span className="text-5xl mb-3">👤</span>
                <p className="text-sm">Sélectionner un contact dans la liste</p>
                <p className="text-xs mt-1 text-gray-300">Les contacts sont créés automatiquement à chaque message WhatsApp reçu</p>
              </div>
            )}
          </div>

        </div>
      </div>
    </AppLayout>
  );
}
