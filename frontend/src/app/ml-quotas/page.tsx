'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface MLQuota {
  id: string;
  plan: string;
  monthly_requests: number;
  daily_requests: number | null;
  max_tokens_per_request: number | null;
  price_per_1000_requests: number | null;
  created_at: string;
  updated_at: string;
}

export default function MLQuotasPage() {
  const { user } = useAuth();
  const [quotas, setQuotas] = useState<MLQuota[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<MLQuota | null>(null);
  const [form, setForm] = useState({
    plan: 'FREE',
    monthly_requests: 0,
    daily_requests: null as number | null,
    max_tokens_per_request: null as number | null,
    price_per_1000_requests: null as number | null,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchQuotas = async () => {
    try {
      const response = await api.get('/ml-quotas');
      setQuotas(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuotas();
  }, []);

  const openEdit = (q: MLQuota) => {
    setEditing(q);
    setForm({
      plan: q.plan,
      monthly_requests: q.monthly_requests,
      daily_requests: q.daily_requests,
      max_tokens_per_request: q.max_tokens_per_request,
      price_per_1000_requests: q.price_per_1000_requests,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setError('');
    setEditing(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      if (editing) {
        await api.put(`/ml-quotas/${editing.plan}`, form);
        setSuccess('Quota mis à jour.');
      } else {
        await api.post('/ml-quotas', form);
        setSuccess('Quota créé.');
      }
      setShowModal(false);
      fetchQuotas();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur');
    } finally {
      setSubmitting(false);
    }
  };

  const getPlanBadgeColor = (plan: string) => {
    switch (plan) {
      case 'FREE': return 'bg-gray-100 text-gray-800';
      case 'BASIC': return 'bg-blue-100 text-blue-800';
      case 'PREMIUM': return 'bg-purple-100 text-purple-800';
      case 'ENTERPRISE': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">🤖 Quotas Machine Learning</h1>
          <button onClick={() => { setEditing(null); setForm({ plan: 'FREE', monthly_requests: 0, daily_requests: null, max_tokens_per_request: null, price_per_1000_requests: null }); setShowModal(true); }}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
            + Créer un quota
          </button>
        </div>

        {success && <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm"><span>{success}</span><button onClick={() => setSuccess('')}>✕</button></div>}
        {error && <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm"><span>{error}</span><button onClick={() => setError('')}>✕</button></div>}

        {loading ? (
          <div className="text-center py-12 text-gray-400">Chargement...</div>
        ) : quotas.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            Aucun quota configuré. <button onClick={() => { setEditing(null); setForm({ plan: 'FREE', monthly_requests: 0, daily_requests: null, max_tokens_per_request: null, price_per_1000_requests: null }); setShowModal(true); }} className="text-green-600 underline">Créer le premier</button>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {['Plan', 'Requêtes/mois', 'Requêtes/jour', 'Max tokens/requête', 'Prix/1000 req', 'Actions'].map(h => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {quotas.map((q) => (
                <tr key={q.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPlanBadgeColor(q.plan)}`}>
                      {q.plan}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {q.monthly_requests === -1 ? 'Illimité' : q.monthly_requests}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {q.daily_requests || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {q.max_tokens_per_request || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {q.price_per_1000_requests ? `${q.price_per_1000_requests / 100}€` : '—'}
                  </td>
                  <td className="px-6 py-4 text-sm space-x-2">
                    <button onClick={() => openEdit(q)} className="text-indigo-600 hover:text-indigo-900 font-medium">Éditer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl">
              <h3 className="font-bold text-gray-900 mb-4">{editing ? '✏️ Modifier le quota' : '🤖 Créer un quota'}</h3>
              <form onSubmit={handleSubmit} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Plan d'abonnement *</label>
                  <select value={form.plan} onChange={e => setForm({ ...form, plan: e.target.value })}
                    disabled={!!editing}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-green-500">
                    <option value="FREE">FREE</option>
                    <option value="BASIC">BASIC</option>
                    <option value="PREMIUM">PREMIUM</option>
                    <option value="ENTERPRISE">ENTERPRISE</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Requêtes mensuelles *</label>
                  <input type="number" required value={form.monthly_requests} onChange={e => setForm({ ...form, monthly_requests: parseInt(e.target.value) })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="0 pour aucun, -1 pour illimité" />
                  <p className="text-xs text-gray-500 mt-1">-1 = illimité, 0 = désactivé</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Requêtes journalières (optionnel)</label>
                  <input type="number" value={form.daily_requests || ''} onChange={e => setForm({ ...form, daily_requests: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="Laisser vide pour illimité" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max tokens par requête (optionnel)</label>
                  <input type="number" value={form.max_tokens_per_request || ''} onChange={e => setForm({ ...form, max_tokens_per_request: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="Ex: 500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prix pour 1000 requêtes en centimes (optionnel)</label>
                  <input type="number" value={form.price_per_1000_requests || ''} onChange={e => setForm({ ...form, price_per_1000_requests: e.target.value ? parseInt(e.target.value) : null })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="Ex: 50 pour 0.50€" />
                </div>
                <div className="flex gap-2 pt-2">
                  <button type="button" onClick={closeModal} className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 text-sm font-medium">Annuler</button>
                  <button type="submit" disabled={submitting} className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50">
                    {submitting ? 'Enregistrement...' : (editing ? 'Mettre à jour' : 'Créer')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
