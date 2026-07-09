// Documents API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Document {
  id: string;
  company_id: string;
  file_name: string;
  file_type: string;
  file_path?: string;
  file_size?: number;
  status: string;
  chunk_count: number;
  processed_at?: string;
  extra_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface IngestionJob {
  id: string;
  company_id: string;
  source_type: string;
  source_config?: Record<string, any>;
  status: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  created_at: string;
  updated_at: string;
}

class DocumentsService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/ml/documents/upload`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload document');
    return response.json();
  }

  async getDocuments(params?: { status_filter?: string; skip?: number; limit?: number }): Promise<Document[]> {
    const queryParams = new URLSearchParams();
    if (params?.status_filter) queryParams.append('status_filter', params.status_filter);
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const response = await fetch(`${API_BASE}/ml/documents?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
  }

  async getDocument(documentId: string): Promise<Document> {
    const response = await fetch(`${API_BASE}/ml/documents/${documentId}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch document');
    return response.json();
  }

  async deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/ml/documents/${documentId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete document');
  }

  async ingestFromDatabase(): Promise<IngestionJob> {
    const response = await fetch(`${API_BASE}/ml/ingestion/from-db`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to ingest from database');
    return response.json();
  }

  async reindexDocuments(): Promise<IngestionJob> {
    const response = await fetch(`${API_BASE}/ml/ingestion/reindex`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to reindex documents');
    return response.json();
  }

  async getIngestionJob(jobId: string): Promise<IngestionJob> {
    const response = await fetch(`${API_BASE}/ml/ingestion/jobs/${jobId}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch ingestion job');
    return response.json();
  }
}

export const documentsService = new DocumentsService();
