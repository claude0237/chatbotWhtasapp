'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface CompanyItem {
  id: string;
  name: string;
}

interface UserItem {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  company_id: string;
  company_name?: string;
  created_at: string;
}

const ALL_ROLES = [
  { value: 'AGENT',         label: 'Agent' },
  { value: 'COMPANY_ADMIN', label: 'Admin Entreprise' },
  { value: 'SUPER_ADMIN',   label: 'Super Admin' },
];

const ROLE_BADGE: Record<string, string> = {
  SUPER_ADMIN:   'bg-purple-100 text-purple-800',
  COMPANY_ADMIN: 'bg-blue-100 text-blue-800',
  AGENT:         'bg-gray-100 text-gray-800',
};

const EMPTY_FORM = { first_name: '', last_name: '', email: '', role: 'AGENT', password: '', company_id: '' };

export default function UsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [companies, setCompanies] = useState<CompanyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<UserItem | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const { user } = useAuth();
  const availableRoles = user?.role === 'SUPER_ADMIN' ? ALL_ROLES : ALL_ROLES.filter(r => r.value !== 'SUPER_ADMIN');

  const parseError = (err: any): string => {
    const detail = err?.response?.data?.detail;
    if (!detail) return 'Erreur inconnue';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d: any) => d.msg || JSON.stringify(d)).join(' | ');
    return JSON.stringify(detail);
  };

  useEffect(() => {
    fetchUsers();
    if (user?.role === 'SUPER_ADMIN') {
      api.get('/companies/').then(res => {
        const data = res.data;
        setCompanies(Array.isArray(data) ? data : (data.companies || data.data || []));
      }).catch(() => {});
    }
  }, [user]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/users/');
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  };

  const openCreate = () => { setEditing(null); setForm({ ...EMPTY_FORM, company_id: user?.company_id || '' }); setShowModal(true); };
  const openEdit = (u: UserItem) => {
    setEditing(u);
    setForm({ first_name: u.first_name, last_name: u.last_name, email: u.email, role: u.role, password: '', company_id: u.company_id });
    setShowModal(true);
  };
  const closeModal = () => { setShowModal(false); setError(''); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true); setError('');
    try {
      const payload: any = { first_name: form.first_name, last_name: form.last_name, email: form.email, role: form.role };
      if (!editing) { payload.company_id = user?.company_id || form.company_id; }
      if (form.password) { payload.password = form.password; }
      if (user?.role === 'SUPER_ADMIN' && form.company_id) { payload.company_id = form.company_id; }
      if (editing) {
        await api.put(`/users/${editing.id}`, payload);
        setSuccess('Utilisateur mis à jour.');
      } else {
        await api.post('/users/', payload);
        setSuccess('Utilisateur créé.');
      }
      closeModal();
      fetchUsers();
    } catch (err: any) {
      setError(parseError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRoleChange = async (u: UserItem, newRole: string) => {
    try {
      await api.put(`/users/${u.id}`, { role: newRole });
      fetchUsers();
    } catch (err: any) {
      setError(parseError(err));
    }
  };

  const handleToggleActive = async (u: UserItem) => {
    try {
      await api.put(`/users/${u.id}`, { is_active: !u.is_active });
      fetchUsers();
    } catch (err: any) {
      setError(parseError(err));
    }
  };

  const handleDelete = async (u: UserItem) => {
    if (!confirm(`Supprimer ${u.first_name} ${u.last_name} ? Cette action est irréversible.`)) return;
    try {
      await api.delete(`/users/${u.id}`);
      setSuccess('Utilisateur supprimé.');
      fetchUsers();
    } catch (err: any) {
      setError(parseError(err));
    }
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">👥 Utilisateurs</h1>
            <p className="text-sm text-gray-500 mt-1">{users.length} utilisateur(s)</p>
          </div>
          <button onClick={openCreate}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
            + Nouvel utilisateur
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-lg mb-4 flex justify-between">
            <span>{error}</span><button onClick={() => setError('')}>✕</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-3 rounded-lg mb-4 flex justify-between">
            <span>✅ {success}</span><button onClick={() => setSuccess('')}>✕</button>
          </div>
        )}

        {/* Table */}
        <div className="bg-white shadow rounded-xl overflow-hidden">
          {loading ? (
            <div className="text-center py-12 text-gray-400">Chargement...</div>
          ) : users.length === 0 ? (
            <div className="text-center py-12 text-gray-400">Aucun utilisateur.</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['Nom', 'Email', 'Entreprise', 'Rôle', 'Statut', 'Créé le', 'Actions'].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((u) => {
                  const isSelf = u.id === user?.id;
                  return (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">{u.first_name} {u.last_name}</div>
                        {isSelf && <span className="text-xs text-green-600">(vous)</span>}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">{u.email}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {u.company_name || (
                          <span className="text-gray-400 italic">Non assigné</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <select
                          value={u.role}
                          onChange={e => handleRoleChange(u, e.target.value)}
                          disabled={isSelf}
                          className={`text-xs border rounded px-2 py-1 font-medium ${ROLE_BADGE[u.role] || 'bg-gray-100'} disabled:opacity-60`}
                        >
                          {availableRoles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {u.is_active ? '✅ Actif' : '🔴 Inactif'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(u.created_at).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2">
                        <button onClick={() => openEdit(u)} className="text-indigo-600 hover:text-indigo-900 font-medium">Éditer</button>
                        <button
                          onClick={() => handleToggleActive(u)}
                          disabled={isSelf}
                          className="text-amber-600 hover:text-amber-900 font-medium disabled:opacity-40"
                        >
                          {u.is_active ? 'Désactiver' : 'Activer'}
                        </button>
                        <button
                          onClick={() => handleDelete(u)}
                          disabled={isSelf}
                          className="text-red-600 hover:text-red-900 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              {editing ? '✏️ Modifier l\'utilisateur' : '👤 Nouvel utilisateur'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prénom *</label>
                  <input type="text" required value={form.first_name}
                    onChange={e => setForm({ ...form, first_name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="Jean"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                  <input type="text" required value={form.last_name}
                    onChange={e => setForm({ ...form, last_name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                    placeholder="Dupont"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" required value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                  placeholder="jean@exemple.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rôle *</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500">
                  {availableRoles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {editing ? 'Nouveau mot de passe (laisser vide pour ne pas changer)' : 'Mot de passe *'}
                </label>
                <input type="password" required={!editing} value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                  placeholder={editing ? 'Laisser vide pour conserver' : 'Minimum 8 caractères'}
                />
              </div>
              {user?.role === 'SUPER_ADMIN' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Entreprise *</label>
                  <select required={!editing} value={form.company_id}
                    onChange={e => setForm({ ...form, company_id: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500">
                    <option value="">-- Sélectionner une entreprise --</option>
                    {companies.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              )}
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
    </AppLayout>
  );
}
