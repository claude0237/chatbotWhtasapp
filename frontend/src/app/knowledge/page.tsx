'use client';

import { useState, useEffect } from 'react';
import { useHashTab } from '../../hooks/useHashTab';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface KnowledgeEntry {
  id: string;
  company_id: string;
  title: string;
  content: string;
  category_id: string | null;
  source_type: string;
  source_id: string | null;
  extra_data: object | null;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface KnowledgeCategory {
  id: string;
  company_id: string;
  name: string;
  parent_id: string | null;
  icon: string | null;
  created_at: string;
  updated_at: string;
}

export default function KnowledgePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [categories, setCategories] = useState<KnowledgeCategory[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useHashTab<'entries' | 'categories'>('entries');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchEntries();
      fetchCategories();
    }
  }, [user, searchQuery, selectedCategory]);

  const fetchEntries = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (selectedCategory) params.append('category_id', selectedCategory);
      
      const response = await api.get(`/knowledge?${params.toString()}`);
      setEntries(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch knowledge entries');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.get('/knowledge/categories');
      setCategories(response.data);
    } catch (err: any) {
      console.error('Failed to fetch categories:', err);
    }
  };

  const handleCreateEntry = async () => {
    const title = prompt('Enter title:');
    const content = prompt('Enter content:');
    if (title && content) {
      try {
        await api.post('/knowledge', {
          title: title,
          content: content,
          category_id: selectedCategory || null
        });
        fetchEntries();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create entry');
      }
    }
  };

  const handleUpdateEntry = async (entryId: string) => {
    const entry = entries.find(e => e.id === entryId);
    if (!entry) return;
    
    const title = prompt('Enter title:', entry.title);
    const content = prompt('Enter content:', entry.content);
    
    if (title || content) {
      try {
        await api.put(`/knowledge/${entryId}`, {
          title: title || undefined,
          content: content || undefined
        });
        fetchEntries();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to update entry');
      }
    }
  };

  const handleDeleteEntry = async (entryId: string) => {
    if (confirm('Are you sure you want to delete this entry?')) {
      try {
        await api.delete(`/knowledge/${entryId}`);
        fetchEntries();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete entry');
      }
    }
  };

  const handleCreateCategory = async () => {
    const name = prompt('Enter category name:');
    if (name) {
      try {
        await api.post('/knowledge/categories', {
          name: name
        });
        fetchCategories();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create category');
      }
    }
  };

  const [showEntryModal, setShowEntryModal]       = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingEntry, setEditingEntry]           = useState<KnowledgeEntry | null>(null);
  const [entryForm, setEntryForm]   = useState({ title: '', content: '', category_id: '' });
  const [categoryForm, setCategoryForm] = useState({ name: '', icon: '' });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess]       = useState('');

  const openCreateEntry = () => { setEditingEntry(null); setEntryForm({ title: '', content: '', category_id: selectedCategory || '' }); setShowEntryModal(true); };
  const openEditEntry   = (e: KnowledgeEntry) => { setEditingEntry(e); setEntryForm({ title: e.title, content: e.content, category_id: e.category_id || '' }); setShowEntryModal(true); };

  const handleSubmitEntry = async (ev: React.FormEvent) => {
    ev.preventDefault(); setSubmitting(true);
    try {
      if (editingEntry) {
        await api.put(`/knowledge/${editingEntry.id}`, { title: entryForm.title, content: entryForm.content, category_id: entryForm.category_id || null });
        setSuccess('Entrée mise à jour.');
      } else {
        await api.post('/knowledge', { title: entryForm.title, content: entryForm.content, category_id: entryForm.category_id || null });
        setSuccess('Entrée créée.');
      }
      setShowEntryModal(false); fetchEntries();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
    finally { setSubmitting(false); }
  };

  const handleSubmitCategory = async (ev: React.FormEvent) => {
    ev.preventDefault(); setSubmitting(true);
    try {
      await api.post('/knowledge/categories', { name: categoryForm.name, icon: categoryForm.icon || null });
      setSuccess('Catégorie créée.'); setShowCategoryModal(false); fetchCategories();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
    finally { setSubmitting(false); }
  };

  if (loading) return (
    <AppLayout><div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div></AppLayout>
  );

  return (
    <AppLayout>
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">📚 Base de connaissances</h1>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm">
            <span>{error}</span><button onClick={() => setError('')}>✕</button>
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm">
            <span>✅ {success}</span><button onClick={() => setSuccess('')}>✕</button>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {(['entries', 'categories'] as const).map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}>
                {tab === 'entries' ? 'Entrées' : 'Catégories'}
              </button>
            ))}
          </nav>
        </div>

        {/* Entries Tab */}
        {activeTab === 'entries' && (
          <div>
            {/* Search and Filter */}
            <div className="bg-white shadow rounded-lg p-4 mb-5 flex gap-3 items-center">
              <input type="text" placeholder="Rechercher..." value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" />
              <select value={selectedCategory || ''} onChange={e => setSelectedCategory(e.target.value || null)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
                <option value="">Toutes catégories</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <button onClick={openCreateEntry}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium whitespace-nowrap">
                + Ajouter
              </button>
            </div>

            {/* Entries List */}
            <div className="bg-white shadow rounded-xl overflow-hidden">
              <div className="divide-y divide-gray-100">
                {entries.length === 0 ? (
                  <div className="px-4 py-10 text-center text-gray-400 text-sm">Aucune entrée trouvée</div>
                ) : entries.map(entry => (
                  <div key={entry.id} onClick={() => setSelectedEntry(entry)}
                    className={`px-5 py-4 cursor-pointer hover:bg-gray-50 ${selectedEntry?.id === entry.id ? 'bg-green-50 border-l-4 border-green-500' : ''}`}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900">{entry.title}</p>
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{entry.content}</p>
                        <p className="text-xs text-gray-400 mt-1">v{entry.version} · {new Date(entry.updated_at).toLocaleDateString('fr-FR')}</p>
                      </div>
                      <div className="flex gap-2 ml-4 flex-shrink-0">
                        <button onClick={e => { e.stopPropagation(); openEditEntry(entry); }}
                          className="text-indigo-600 hover:text-indigo-900 text-xs font-medium">Éditer</button>
                        <button onClick={e => { e.stopPropagation(); if (confirm('Supprimer cette entrée ?')) handleDeleteEntry(entry.id); }}
                          className="text-red-600 hover:text-red-900 text-xs font-medium">Supprimer</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Entry Detail */}
            {selectedEntry && (
              <div className="bg-white shadow rounded-xl p-6 mt-5">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-lg font-bold text-gray-900">{selectedEntry.title}</h2>
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">v{selectedEntry.version}</span>
                </div>
                <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{selectedEntry.content}</div>
                <p className="text-xs text-gray-400 mt-4">Mis à jour le {new Date(selectedEntry.updated_at).toLocaleString('fr-FR')}</p>
              </div>
            )}
          </div>
        )}

        {/* Categories Tab */}
        {activeTab === 'categories' && (
          <div className="bg-white shadow rounded-xl p-6">
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-lg font-bold text-gray-900">Catégories</h2>
              <button onClick={() => { setCategoryForm({ name: '', icon: '' }); setShowCategoryModal(true); }}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
                + Nouvelle catégorie
              </button>
            </div>
            {categories.length === 0 ? (
              <div className="text-center py-10 text-gray-400 text-sm">Aucune catégorie</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {categories.map(cat => (
                  <div key={cat.id} className="border border-gray-200 rounded-xl p-4 flex items-center gap-3">
                    <span className="text-3xl">{cat.icon || '📁'}</span>
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{cat.name}</p>
                      <p className="text-xs text-gray-400">{new Date(cat.created_at).toLocaleDateString('fr-FR')}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal Entrée */}
      {showEntryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-xl shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">{editingEntry ? '✏️ Modifier l\'entrée' : '+ Nouvelle entrée'}</h3>
            <form onSubmit={handleSubmitEntry} className="space-y-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Titre *</label>
                <input required value={entryForm.title} onChange={e => setEntryForm({...entryForm, title: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Titre de l'entrée" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Contenu *</label>
                <textarea required value={entryForm.content} onChange={e => setEntryForm({...entryForm, content: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" rows={6} placeholder="Contenu de l'entrée de connaissance..." /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Catégorie</label>
                <select value={entryForm.category_id} onChange={e => setEntryForm({...entryForm, category_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="">Aucune catégorie</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select></div>
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowEntryModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">{submitting ? '...' : editingEntry ? 'Mettre à jour' : 'Créer'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Catégorie */}
      {showCategoryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">+ Nouvelle catégorie</h3>
            <form onSubmit={handleSubmitCategory} className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                <input required value={categoryForm.name} onChange={e => setCategoryForm({...categoryForm, name: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500" placeholder="Ex: FAQ, Produits..." /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Icône (emoji)</label>
                <input value={categoryForm.icon} onChange={e => setCategoryForm({...categoryForm, icon: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="📁" /></div>
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowCategoryModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">{submitting ? '...' : 'Créer'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
