// Analytics API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DashboardData {
  conversations_today: number;
  messages_sent: number;
  avg_response_time: number;
  new_customers: number;
  ml_enabled: boolean;
  active_agents: number;
  date: string;
}

export interface SuperAdminDashboardData {
  total_companies: number;
  total_users: number;
  total_conversations: number;
  platform_usage: number;
  date: string;
}

export interface ConversationStats {
  total_conversations: number;
  conversations_in_period: number;
  status_breakdown: Record<string, number>;
  start_date: string;
  end_date: string;
}

export interface MessageStats {
  total_messages: number;
  sender_breakdown: Record<string, number>;
  start_date: string;
  end_date: string;
}

export interface AgentPerformance {
  agent_id: string;
  agent_name: string;
  messages_sent: number;
  conversations_handled: number;
  avg_messages_per_conversation: number;
}

export interface MLPerformance {
  total_ml_responses: number;
  total_native_responses: number;
  average_confidence: number;
  ml_response_rate: number;
  start_date: string;
  end_date: string;
}

export interface ResponseTimeStats {
  average_response_time: number;
  min_response_time: number;
  max_response_time: number;
  total_responses: number;
}

class AnalyticsService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getDashboard(): Promise<DashboardData> {
    const response = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch dashboard');
    return response.json();
  }

  async getSuperAdminDashboard(): Promise<SuperAdminDashboardData> {
    const response = await fetch(`${API_BASE}/analytics/super-admin/dashboard`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch super admin dashboard');
    return response.json();
  }

  async getConversationStats(params?: { start_date?: string; end_date?: string }): Promise<ConversationStats> {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE}/analytics/conversations?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch conversation stats');
    return response.json();
  }

  async getMessageStats(params?: { start_date?: string; end_date?: string }): Promise<MessageStats> {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE}/analytics/messages?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch message stats');
    return response.json();
  }

  async getAgentPerformance(params?: { start_date?: string; end_date?: string }): Promise<AgentPerformance[]> {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE}/analytics/agents?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch agent performance');
    return response.json();
  }

  async getMLPerformance(params?: { start_date?: string; end_date?: string }): Promise<MLPerformance> {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE}/analytics/ml?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch ML performance');
    return response.json();
  }

  async getResponseTimeStats(params?: { start_date?: string; end_date?: string }): Promise<ResponseTimeStats> {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE}/analytics/response-time?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch response time stats');
    return response.json();
  }

  async generateReport(params: { report_name: string; report_type: string; start_date?: string; end_date?: string }): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('report_name', params.report_name);
    queryParams.append('report_type', params.report_type);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);

    const response = await fetch(`${API_BASE}/analytics/reports?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to generate report');
    return response.json();
  }
}

export const analyticsService = new AnalyticsService();
