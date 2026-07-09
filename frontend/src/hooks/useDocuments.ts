import { useState, useEffect } from 'react';
import { documentsService, Document, IngestionJob } from '../services/documents';

export function useDocuments(params?: { status_filter?: string; skip?: number; limit?: number }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const data = await documentsService.getDocuments(params);
      setDocuments(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const uploadDocument = async (file: File) => {
    try {
      const uploaded = await documentsService.uploadDocument(file);
      setDocuments([...documents, uploaded]);
      return uploaded;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to upload document');
    }
  };

  const deleteDocument = async (documentId: string) => {
    try {
      await documentsService.deleteDocument(documentId);
      setDocuments(documents.filter(d => d.id !== documentId));
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete document');
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [params?.status_filter, params?.skip, params?.limit]);

  return {
    documents,
    loading,
    error,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
  };
}

export function useIngestion() {
  const [job, setJob] = useState<IngestionJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const ingestFromDatabase = async () => {
    try {
      setLoading(true);
      const data = await documentsService.ingestFromDatabase();
      setJob(data);
      setError('');
      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to ingest from database');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reindexDocuments = async () => {
    try {
      setLoading(true);
      const data = await documentsService.reindexDocuments();
      setJob(data);
      setError('');
      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to reindex documents');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getJobStatus = async (jobId: string) => {
    try {
      const data = await documentsService.getIngestionJob(jobId);
      setJob(data);
      setError('');
      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to fetch job status');
      throw err;
    }
  };

  return {
    job,
    loading,
    error,
    ingestFromDatabase,
    reindexDocuments,
    getJobStatus,
  };
}
