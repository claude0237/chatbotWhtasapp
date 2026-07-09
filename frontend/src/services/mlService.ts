import api from '../lib/api';

export interface MLModel {
  id: string;
  company_id: string;
  name: string;
  model_type: string;
  provider: string;
  model_name: string;
  version?: string;
  configuration?: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingRequest {
  training_data: Array<{ text: string; intent: string }>;
  model_name: string;
  hyperparameters?: any;
}

export interface FineTuningRequest {
  training_data: Array<{ prompt: string; completion: string }>;
  base_model?: string;
  model_name: string;
  hyperparameters?: any;
}

export interface EvaluationRequest {
  test_data: Array<{ text: string; intent: string }>;
}

export interface EvaluationResult {
  model_id: string;
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  classification_report?: string;
  test_samples: number;
}

export const mlService = {
  async trainIntentClassifier(request: TrainingRequest): Promise<MLModel> {
    const response = await api.post('/ml/train/intent-classifier', request);
    return response.data;
  },

  async fineTuneLLM(request: FineTuningRequest): Promise<MLModel> {
    const response = await api.post('/ml/train/fine-tune-llm', request);
    return response.data;
  },

  async evaluateModel(modelId: string, request: EvaluationRequest): Promise<EvaluationResult> {
    const response = await api.post(`/ml/evaluate/${modelId}`, request);
    return response.data;
  },

  async getMLModels(skip = 0, limit = 100): Promise<MLModel[]> {
    const response = await api.get('/ml/models', { params: { skip, limit } });
    return response.data;
  },

  async deployModel(modelId: string): Promise<MLModel> {
    const response = await api.post(`/ml/models/${modelId}/deploy`);
    return response.data;
  }
};
