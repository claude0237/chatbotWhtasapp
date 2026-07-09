import { useState, useEffect } from 'react';
import { analyticsService, DashboardData, SuperAdminDashboardData, ConversationStats, MessageStats, AgentPerformance, MLPerformance, ResponseTimeStats } from '../services/analytics';

export function useDashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getDashboard();
      setDashboard(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return {
    dashboard,
    loading,
    error,
    fetchDashboard,
  };
}

export function useSuperAdminDashboard() {
  const [dashboard, setDashboard] = useState<SuperAdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getSuperAdminDashboard();
      setDashboard(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch super admin dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  return {
    dashboard,
    loading,
    error,
    fetchDashboard,
  };
}

export function useAnalytics(params?: { start_date?: string; end_date?: string }) {
  const [conversationStats, setConversationStats] = useState<ConversationStats | null>(null);
  const [messageStats, setMessageStats] = useState<MessageStats | null>(null);
  const [agentPerformance, setAgentPerformance] = useState<AgentPerformance[]>([]);
  const [mlPerformance, setMLPerformance] = useState<MLPerformance | null>(null);
  const [responseTimeStats, setResponseTimeStats] = useState<ResponseTimeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [convStats, msgStats, agentPerf, mlPerf, respTime] = await Promise.all([
        analyticsService.getConversationStats(params),
        analyticsService.getMessageStats(params),
        analyticsService.getAgentPerformance(params),
        analyticsService.getMLPerformance(params),
        analyticsService.getResponseTimeStats(params),
      ]);
      setConversationStats(convStats);
      setMessageStats(msgStats);
      setAgentPerformance(agentPerf);
      setMLPerformance(mlPerf);
      setResponseTimeStats(respTime);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [params?.start_date, params?.end_date]);

  return {
    conversationStats,
    messageStats,
    agentPerformance,
    mlPerformance,
    responseTimeStats,
    loading,
    error,
    fetchAnalytics,
  };
}
