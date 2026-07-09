// Knowledge Base API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface KnowledgeEntry {
  id: string;
  company_id: string;
  title: string;
  content: string;
  category_id?: string;
  source_type: string;
  source_id?: string;
  metadata?: Record<string, any>;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeCategory {
  id: string;
  company_id: string;
  name: string;
  parent_id?: string;
  icon?: string;
  created_at: string;
  updated_at: string;
}

class KnowledgeService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getKnowledgeEntries(params?: { category_id?: string; search?: string; skip?: number; limit?: number }): Promise<KnowledgeEntry[]> {
    const queryParams = new URLSearchParams();
    if (params?.category_id) queryParams.append('category_id', params.category_id);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const response = await fetch(`${API_BASE}/knowledge/?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch knowledge entries');
    return response.json();
  }

  async createKnowledgeEntry(data: Partial<KnowledgeEntry>): Promise<KnowledgeEntry> {
    const response = await fetch(`${API_BASE}/knowledge/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create knowledge entry');
    return response.json();
  }

  async updateKnowledgeEntry(entryId: string, data: Partial<KnowledgeEntry>): Promise<KnowledgeEntry> {
    const response = await fetch(`${API_BASE}/knowledge/${entryId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update knowledge entry');
    return response.json();
  }

  async deleteKnowledgeEntry(entryId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/knowledge/${entryId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete knowledge entry');
  }

  async getKnowledgeCategories(skip = 0, limit = 100): Promise<KnowledgeCategory[]> {
    const response = await fetch(`${API_BASE}/knowledge/categories?skip=${skip}&limit=${limit}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch knowledge categories');
    return response.json();
  }

  async createKnowledgeCategory(data: Partial<KnowledgeCategory>): Promise<KnowledgeCategory> {
    const response = await fetch(`${API_BASE}/knowledge/categories`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create knowledge category');
    return response.json();
  }

  async updateKnowledgeCategory(categoryId: string, data: Partial<KnowledgeCategory>): Promise<KnowledgeCategory> {
    const response = await fetch(`${API_BASE}/knowledge/categories/${categoryId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update knowledge category');
    return response.json();
  }

  async deleteKnowledgeCategory(categoryId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/knowledge/categories/${categoryId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete knowledge category');
  }
}

export const knowledgeService = new KnowledgeService();
