// Bot API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface BotConfiguration {
  id: string;
  company_id: string;
  bot_type: string;
  name: string;
  welcome_message?: string;
  away_message?: string;
  closing_message?: string;
  unknown_message?: string;
  language: string;
  timezone: string;
  avatar_url?: string;
  native_rules?: Record<string, any>;
  ml_enabled?: boolean;
  ml_provider?: string;
  ml_model?: string;
  ml_temperature?: string;
  ml_max_tokens?: number;
  fallback_strategy?: string;
  confidence_threshold?: string;
  created_at: string;
  updated_at: string;
}

export interface BotScenario {
  id: string;
  bot_configuration_id: string;
  name: string;
  trigger_keyword: string;
  steps: any[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BotKeyword {
  id: string;
  bot_configuration_id: string;
  keyword: string;
  response: string;
  category?: string;
  created_at: string;
  updated_at: string;
}

class BotService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getBotConfig(): Promise<BotConfiguration> {
    const response = await fetch(`${API_BASE}/bot/config`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch bot configuration');
    return response.json();
  }

  async createBotConfig(data: Partial<BotConfiguration>): Promise<BotConfiguration> {
    const response = await fetch(`${API_BASE}/bot/config`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create bot configuration');
    return response.json();
  }

  async updateBotConfig(data: Partial<BotConfiguration>): Promise<BotConfiguration> {
    const response = await fetch(`${API_BASE}/bot/config`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update bot configuration');
    return response.json();
  }

  async getScenarios(): Promise<BotScenario[]> {
    const response = await fetch(`${API_BASE}/bot/scenarios`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch scenarios');
    return response.json();
  }

  async createScenario(data: Partial<BotScenario>): Promise<BotScenario> {
    const response = await fetch(`${API_BASE}/bot/scenarios`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create scenario');
    return response.json();
  }

  async updateScenario(scenarioId: string, data: Partial<BotScenario>): Promise<BotScenario> {
    const response = await fetch(`${API_BASE}/bot/scenarios/${scenarioId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update scenario');
    return response.json();
  }

  async deleteScenario(scenarioId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/bot/scenarios/${scenarioId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete scenario');
  }

  async getKeywords(): Promise<BotKeyword[]> {
    const response = await fetch(`${API_BASE}/bot/keywords`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch keywords');
    return response.json();
  }

  async createKeyword(data: Partial<BotKeyword>): Promise<BotKeyword> {
    const response = await fetch(`${API_BASE}/bot/keywords`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create keyword');
    return response.json();
  }

  async updateKeyword(keywordId: string, data: Partial<BotKeyword>): Promise<BotKeyword> {
    const response = await fetch(`${API_BASE}/bot/keywords/${keywordId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update keyword');
    return response.json();
  }

  async deleteKeyword(keywordId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/bot/keywords/${keywordId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete keyword');
  }
}

export const botService = new BotService();
