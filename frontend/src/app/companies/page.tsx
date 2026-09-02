'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface Company {
  id: string;
  name: string;
  slug: string;
  description: string;
  email: string;
  is_active: boolean;
  is_suspended: boolean;
  ml_enabled: boolean;
  subscription_plan: string;
  created_at: string;
}

const EMPTY_FORM = { name: '', slug: '', email: '', phone: '', description: '', website: '', logo_url: '', address: '', timezone: 'Africa/Douala', language: 'fr', currency: 'XAF', theme_color: '#3b82f6', ml_enabled: false, subscription_plan: 'FREE' };

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Company | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Company | null>(null);
  const { user } = useAuth();

  useEffect(() => { fetchCompanies(); }, []);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/companies/');
      setCompanies(response.data);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail;
      setError(errorMessage || 'Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setShowModal(true); };
  const openEdit = (c: Company) => { setEditing(c); setForm({ name: c.name, slug: c.slug || '', email: c.email || '', phone: (c as any).phone || '', description: c.description || '', website: (c as any).website || '', logo_url: (c as any).logo_url || '', address: (c as any).address || '', timezone: (c as any).timezone || 'Africa/Douala', language: (c as any).language || 'fr', currency: (c as any).currency || 'XAF', theme_color: (c as any).theme_color || '#3b82f6', ml_enabled: c.ml_enabled || false, subscription_plan: c.subscription_plan || 'FREE' }); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setError(''); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true); setError('');
    try {
      if (editing) {
        // Filter out empty string values for optional fields
        const updateData = Object.fromEntries(
          Object.entries(form).filter(([_, v]) => v !== '')
        );
        await api.put(`/companies/${editing.id}`, updateData);
        setSuccess('Entreprise mise à jour.');
      } else {
        const slug = form.slug || form.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        await api.post('/companies/', { ...form, slug });
        setSuccess('Entreprise créée.');
      }
      closeModal();
      fetchCompanies();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail;
      setError(errorMessage || 'Erreur lors de la sauvegarde');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (c: Company) => {
    try {
      await api.put(`/companies/${c.id}`, { is_active: !c.is_active, is_suspended: c.is_active });
      fetchCompanies();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail;
      setError(errorMessage || 'Erreur');
    }
  };

  const handleDelete = async (c: Company) => {
    console.log('handleDelete called for company:', c);
    setConfirmDelete(c);
    console.log('confirmDelete state set to:', c);
  };

  const confirmDeleteAction = async () => {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await api.delete(`/companies/${confirmDelete.id}`);
      setSuccess('Entreprise supprimée.');
      setConfirmDelete(null);
      fetchCompanies();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail;
      setError(errorMessage || 'Erreur');
    } finally {
      setDeleting(false);
    }
  };

  if (user?.role !== 'SUPER_ADMIN') {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-red-600 text-lg font-medium">⛔ Accès réservé au Super Admin</div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🏢 Entreprises</h1>
            <p className="text-sm text-gray-500 mt-1">{companies.length} entreprise(s)</p>
          </div>
          <button
            onClick={openCreate}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium"
          >
            + Nouvelle entreprise
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-lg mb-4 flex justify-between">
            <span>{error}</span>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-3 rounded-lg mb-4 flex justify-between">
            <span>✅ {success}</span>
            <button onClick={() => setSuccess('')}>✕</button>
          </div>
        )}

        {/* Table */}
        <div className="bg-white shadow rounded-xl overflow-hidden">
          {loading ? (
            <div className="text-center py-12 text-gray-400">Chargement...</div>
          ) : companies.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              Aucune entreprise. <button onClick={openCreate} className="text-green-600 underline">Créer la première</button>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['Nom', 'Email', 'Statut', 'Plan', 'ML', 'Créée le', 'Actions'].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {companies.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{c.name}</div>
                      <div className="text-xs text-gray-400">{c.slug}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{c.email || '—'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        c.is_active && !c.is_suspended ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {c.is_active && !c.is_suspended ? '✅ Active' : '🔴 Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        c.subscription_plan === 'FREE' ? 'bg-gray-100 text-gray-800' :
                        c.subscription_plan === 'BASIC' ? 'bg-blue-100 text-blue-800' :
                        c.subscription_plan === 'PREMIUM' ? 'bg-purple-100 text-purple-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {c.subscription_plan}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        c.ml_enabled ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {c.ml_enabled ? '🤖 ON' : 'OFF'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(c.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <button onClick={() => openEdit(c)} className="text-indigo-600 hover:text-indigo-900 font-medium">Éditer</button>
                      {c.slug !== 'system' && <>
                        <button onClick={() => handleToggle(c)} className="text-amber-600 hover:text-amber-900 font-medium">
                          {c.is_active ? 'Désactiver' : 'Activer'}
                        </button>
                        <button onClick={() => handleDelete(c)} className="text-red-600 hover:text-red-900 font-medium">Supprimer</button>
                      </>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal Create/Edit */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              {editing ? '✏️ Modifier l\'entreprise' : '🏢 Nouvelle entreprise'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                  <input type="text" required value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="Nom de l'entreprise" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Slug <span className="text-gray-400">(auto)</span></label>
                  <input type="text" value={form.slug}
                    onChange={e => setForm({ ...form, slug: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                    placeholder={form.name ? form.name.toLowerCase().replace(/[^a-z0-9]+/g, '-') : 'mon-entreprise'} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input type="email" value={form.email}
                    onChange={e => setForm({ ...form, email: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    placeholder="contact@entreprise.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                  <input type="text" value={form.phone}
                    onChange={e => setForm({ ...form, phone: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    placeholder="+237 6XX XXX XXX" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Adresse</label>
                <input type="text" value={form.address}
                  onChange={e => setForm({ ...form, address: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="Zone Industrielle, Douala" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Site web</label>
                  <input type="text" value={form.website}
                    onChange={e => setForm({ ...form, website: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    placeholder="https://monsite.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Logo</label>
                  <div className="flex items-center gap-2">
                    {form.logo_url && <img src={form.logo_url} alt="logo" className="h-8 w-8 rounded object-cover border" />}
                    <label className="cursor-pointer bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 font-medium">
                      {form.logo_url ? 'Changer' : 'Uploader'}
                      <input type="file" accept="image/*" className="hidden" onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        const formData = new FormData();
                        formData.append('file', file);
                        try {
                          const res = await api.post('/upload/image', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
                          setForm(prev => ({ ...prev, logo_url: res.data.url }));
                        } catch (err: any) { setError(err.response?.data?.detail || 'Erreur upload logo'); }
                      }} />
                    </label>
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  rows={2} placeholder="Description (optionnel)" />
              </div>
              <div className="border-t pt-3 mt-1">
                <p className="text-xs font-semibold text-gray-500 mb-2">⚙️ Paramètres de l'entreprise</p>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Plan d'abonnement</label>
                    <select value={form.subscription_plan} onChange={e => setForm({ ...form, subscription_plan: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs bg-white focus:ring-2 focus:ring-green-500">
                      <option value="FREE">FREE (Gratuit - Sans ML)</option>
                      <option value="BASIC">BASIC (ML limité)</option>
                      <option value="PREMIUM">PREMIUM (ML complet)</option>
                      <option value="ENTERPRISE">ENTERPRISE (ML illimité)</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="ml_enabled" checked={form.ml_enabled}
                      onChange={e => setForm({ ...form, ml_enabled: e.target.checked })}
                      disabled={form.subscription_plan === 'FREE'}
                      className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500 disabled:opacity-50" />
                    <label htmlFor="ml_enabled" className="text-sm font-medium text-gray-700">Activer ML</label>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Fuseau horaire</label>
                    <input type="text" value={form.timezone}
                      onChange={e => setForm({ ...form, timezone: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs"
                      placeholder="Africa/Douala" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Langue</label>
                    <input type="text" value={form.language}
                      onChange={e => setForm({ ...form, language: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs"
                      placeholder="fr" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Devise</label>
                    <input type="text" value={form.currency}
                      onChange={e => setForm({ ...form, currency: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs"
                      placeholder="XAF" />
                  </div>
                </div>
                <div className="mt-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Couleur thème</label>
                  <div className="flex items-center gap-2">
                    <input type="color" value={form.theme_color}
                      onChange={e => setForm({ ...form, theme_color: e.target.value })}
                      className="h-8 w-10 rounded border border-gray-300 cursor-pointer" />
                    <span className="text-xs text-gray-500 font-mono">{form.theme_color}</span>
                  </div>
                </div>
              </div>
              {error && <p className="text-red-600 text-sm">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal}
                  className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-50 text-sm font-medium">
                  Annuler
                </button>
                <button type="submit" disabled={submitting}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm font-medium">
                  {submitting ? 'Enregistrement...' : editing ? 'Mettre à jour' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Confirm Delete Modal */}
      {confirmDelete && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm">
            <h2 className="text-lg font-bold text-gray-900 mb-2">🗑️ Confirmer la suppression</h2>
            <p className="text-sm text-gray-600 mb-4">Supprimer <strong>{confirmDelete.name}</strong> ? Cette action est irréversible.</p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDelete(null)} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-50 text-sm font-medium">Annuler</button>
              <button onClick={confirmDeleteAction} className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 text-sm font-medium">Supprimer</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </AppLayout>
  );
}
