// ML API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface MLModel {
  id: string;
  company_id: string;
  name: string;
  model_type: string;
  provider: string;
  model_name: string;
  version?: string;
  configuration?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingRequest {
  training_data: any[];
  model_name: string;
  hyperparameters?: any;
}

export interface FineTuningRequest {
  training_data: any[];
  base_model: string;
  model_name: string;
  hyperparameters?: any;
}

export interface EvaluationRequest {
  test_data: any[];
}

export interface EvaluationResult {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  confusion_matrix?: any;
  [key: string]: any;
}

class MLService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getMLModels(skip = 0, limit = 100): Promise<MLModel[]> {
    const response = await fetch(`${API_BASE}/ml/models?skip=${skip}&limit=${limit}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch ML models');
    return response.json();
  }

  async trainIntentClassifier(request: TrainingRequest): Promise<MLModel> {
    const response = await fetch(`${API_BASE}/ml/train/intent-classifier`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to train intent classifier');
    return response.json();
  }

  async fineTuneLLM(request: FineTuningRequest): Promise<MLModel> {
    const response = await fetch(`${API_BASE}/ml/train/fine-tune-llm`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to fine-tune LLM');
    return response.json();
  }

  async evaluateModel(modelId: string, request: EvaluationRequest): Promise<EvaluationResult> {
    const response = await fetch(`${API_BASE}/ml/evaluate/${modelId}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to evaluate model');
    return response.json();
  }

  async deployModel(modelId: string): Promise<MLModel> {
    const response = await fetch(`${API_BASE}/ml/models/${modelId}/deploy`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to deploy model');
    return response.json();
  }
}

export const mlService = new MLService();
