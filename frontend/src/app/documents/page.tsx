'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';

interface Document {
  id: string;
  company_id: string;
  file_name: string;
  file_type: string;
  file_path: string | null;
  file_size: number | null;
  status: string;
  chunk_count: number;
  processed_at: string | null;
  extra_data: object | null;
  created_at: string;
  updated_at: string;
}

interface IngestionJob {
  id: string;
  company_id: string;
  source_type: string;
  source_config: object | null;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  created_at: string;
  updated_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchDocuments();
      fetchJobs();
    }
  }, [user]);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/ml/documents');
      setDocuments(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const response = await api.get('/ml/ingestion/jobs');
      setJobs(response.data);
    } catch (err: any) {
      console.error('Failed to fetch jobs:', err);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      await api.post('/ml/documents/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });

      await fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      try {
        await api.delete(`/ml/documents/${documentId}`);
        fetchDocuments();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete document');
      }
    }
  };

  const handleIngestFromDatabase = async () => {
    if (confirm('This will ingest all knowledge base entries. Continue?')) {
      try {
        await api.post('/ml/ingestion/from-db');
        fetchJobs();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to start ingestion');
      }
    }
  };

  const handleReindex = async () => {
    if (confirm('This will reindex all documents. Continue?')) {
      try {
        await api.post('/ml/ingestion/reindex');
        fetchJobs();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to start reindex');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Documents</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Upload Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Document</h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              onChange={handleFileUpload}
              accept=".pdf,.doc,.docx,.xlsx,.xls,.md,.txt,.html"
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {uploading ? 'Uploading...' : 'Choose File'}
            </label>
            <p className="text-sm text-gray-500 mt-2">
              Supported formats: PDF, Word, Excel, Markdown, TXT, HTML
            </p>
          </div>

          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Ingestion Actions */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Ingestion Actions</h2>
          <div className="flex gap-4">
            <button
              onClick={handleIngestFromDatabase}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
            >
              Ingest from Knowledge Base
            </button>
            <button
              onClick={handleReindex}
              className="bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700"
            >
              Reindex All Documents
            </button>
          </div>
        </div>

        {/* Documents List */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Documents</h2>
          
          <div className="space-y-4">
            {documents.map((document) => (
              <div key={document.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">{document.file_name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Type: {document.file_type} • Size: {document.file_size ? `${(document.file_size / 1024).toFixed(2)} KB` : 'Unknown'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Status: {document.status} • Chunks: {document.chunk_count}
                    </div>
                    {document.processed_at && (
                      <div className="text-xs text-gray-400 mt-1">
                        Processed: {new Date(document.processed_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteDocument(document.id)}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
            {documents.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                No documents uploaded yet
              </div>
            )}
          </div>
        </div>

        {/* Ingestion Jobs */}
        {jobs.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6 mt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Ingestion Jobs</h2>
            
            <div className="space-y-4">
              {jobs.map((job) => (
                <div key={job.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{job.source_type}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Status: {job.status} • Progress: {job.processed_documents}/{job.total_documents}
                      </div>
                      {job.failed_documents > 0 && (
                        <div className="text-xs text-red-500 mt-1">
                          Failed: {job.failed_documents}
                        </div>
                      )}
                      {job.error_message && (
                        <div className="text-xs text-red-500 mt-1">
                          Error: {job.error_message}
                        </div>
                      )}
                    </div>
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      job.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                      job.status === 'RUNNING' ? 'bg-blue-100 text-blue-800' :
                      job.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
