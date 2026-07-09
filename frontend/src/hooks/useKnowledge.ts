import { useState, useEffect } from 'react';
import { knowledgeService, KnowledgeEntry, KnowledgeCategory } from '../services/knowledge';

export function useKnowledge(params?: { category_id?: string; search?: string; skip?: number; limit?: number }) {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchEntries = async () => {
    try {
      setLoading(true);
      const data = await knowledgeService.getKnowledgeEntries(params);
      setEntries(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch knowledge entries');
    } finally {
      setLoading(false);
    }
  };

  const createEntry = async (data: Partial<KnowledgeEntry>) => {
    try {
      const created = await knowledgeService.createKnowledgeEntry(data);
      setEntries([...entries, created]);
      return created;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to create knowledge entry');
    }
  };

  const updateEntry = async (entryId: string, data: Partial<KnowledgeEntry>) => {
    try {
      const updated = await knowledgeService.updateKnowledgeEntry(entryId, data);
      setEntries(entries.map(e => e.id === entryId ? updated : e));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update knowledge entry');
    }
  };

  const deleteEntry = async (entryId: string) => {
    try {
      await knowledgeService.deleteKnowledgeEntry(entryId);
      setEntries(entries.filter(e => e.id !== entryId));
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete knowledge entry');
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [params?.category_id, params?.search, params?.skip, params?.limit]);

  return {
    entries,
    loading,
    error,
    fetchEntries,
    createEntry,
    updateEntry,
    deleteEntry,
  };
}

export function useKnowledgeCategories(skip = 0, limit = 100) {
  const [categories, setCategories] = useState<KnowledgeCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const data = await knowledgeService.getKnowledgeCategories(skip, limit);
      setCategories(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch knowledge categories');
    } finally {
      setLoading(false);
    }
  };

  const createCategory = async (data: Partial<KnowledgeCategory>) => {
    try {
      const created = await knowledgeService.createKnowledgeCategory(data);
      setCategories([...categories, created]);
      return created;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to create knowledge category');
    }
  };

  const updateCategory = async (categoryId: string, data: Partial<KnowledgeCategory>) => {
    try {
      const updated = await knowledgeService.updateKnowledgeCategory(categoryId, data);
      setCategories(categories.map(c => c.id === categoryId ? updated : c));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update knowledge category');
    }
  };

  const deleteCategory = async (categoryId: string) => {
    try {
      await knowledgeService.deleteKnowledgeCategory(categoryId);
      setCategories(categories.filter(c => c.id !== categoryId));
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete knowledge category');
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [skip, limit]);

  return {
    categories,
    loading,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  };
}
