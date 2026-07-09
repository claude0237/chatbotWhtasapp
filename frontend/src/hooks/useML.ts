import { useState, useEffect } from 'react';
import { mlService, MLModel, TrainingRequest, FineTuningRequest, EvaluationRequest, EvaluationResult } from '../services/mlService';

export function useML() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchModels = async () => {
    setLoading(true);
    try {
      const data = await mlService.getMLModels();
      setModels(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch ML models');
    } finally {
      setLoading(false);
    }
  };

  const trainIntentClassifier = async (request: TrainingRequest) => {
    setLoading(true);
    try {
      const model = await mlService.trainIntentClassifier(request);
      await fetchModels();
      return model;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Training failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const fineTuneLLM = async (request: FineTuningRequest) => {
    setLoading(true);
    try {
      const model = await mlService.fineTuneLLM(request);
      await fetchModels();
      return model;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fine-tuning failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const evaluateModel = async (modelId: string, request: EvaluationRequest) => {
    setLoading(true);
    try {
      const result = await mlService.evaluateModel(modelId, request);
      return result;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Evaluation failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deployModel = async (modelId: string) => {
    setLoading(true);
    try {
      const model = await mlService.deployModel(modelId);
      await fetchModels();
      return model;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Deployment failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return {
    models,
    loading,
    error,
    fetchModels,
    trainIntentClassifier,
    fineTuneLLM,
    evaluateModel,
    deployModel
  };
}
