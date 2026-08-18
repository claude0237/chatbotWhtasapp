'use client';

import { useState, useEffect } from 'react';
import { useHashTab } from '../../hooks/useHashTab';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface WhatsAppMessage {
  id: string; message_id: string; direction: string; status: string;
  message_type: string; phone_number: string; display_name: string;
  content: string; created_at: string;
}
interface WhatsAppTemplate {
  id: string; name: string; category: string; language: string; is_approved: boolean;
}
interface WACredentials {
  configured: boolean; channel_id?: string; status?: string;
  phone_number_id?: string; waba_id?: string;
  display_phone_number?: string; access_token_masked?: string;
  meta_app_id?: string; meta_app_secret_masked?: string;
  meta_business_id?: string; webhook_verify_token?: string;
  webhook_url?: string;
}
interface PerformanceStats {
  company_id: string;
  company_name: string;
  total_messages_incoming: number;
  total_messages_outgoing: number;
  total_messages_failed: number;
  success_rate: number;
  avg_response_time_seconds?: number;
  total_contacts: number;
  new_contacts_period: number;
  daily_stats: Array<{ date: string; incoming: number; outgoing: number; failed: number; new_contacts: number }>;
}

interface WebhookStats {
  company_id: string;
  company_name: string;
  configured: boolean;
  webhook_url?: string;
  last_message_received?: string;
  last_message_sent?: string;
  messages_incoming_24h: number;
  messages_outgoing_24h: number;
  messages_failed_24h: number;
  api_connection_status: string;
  phone_number_id?: string;
  status: string;
}

function SuperAdminWebhookPanel() {
  const [activeTab, setActiveTab] = useState<'webhooks' | 'performance'>('webhooks');
  const [webhookStats, setWebhookStats] = useState<WebhookStats[]>([]);
  const [performanceStats, setPerformanceStats] = useState<PerformanceStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [daysPeriod, setDaysPeriod] = useState(30);
  const [chartType, setChartType] = useState<'line' | 'bar'>('line');

  useEffect(() => {
    fetchWebhookStats();
    fetchPerformanceStats();
  }, [daysPeriod]);

  const fetchWebhookStats = async () => {
    try {
      const r = await api.get('/whatsapp/admin/webhook-stats');
      setWebhookStats(r.data.stats);
    } catch (err: unknown) {
      console.error('Failed to fetch webhook stats:', err);
    } finally { 
      setLoading(false); 
      setRefreshing(false);
    }
  };

  const fetchPerformanceStats = async () => {
    try {
      const r = await api.get('/whatsapp/admin/performance-stats', { params: { days: daysPeriod } });
      setPerformanceStats(r.data.stats);
    } catch (err: unknown) {
      console.error('Failed to fetch performance stats:', err);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchWebhookStats();
    fetchPerformanceStats();
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-yellow-100 text-yellow-800',
      dead: 'bg-red-100 text-red-800',
      not_configured: 'bg-gray-100 text-gray-800',
      no_messages: 'bg-gray-100 text-gray-800',
    };
    const labels: Record<string, string> = {
      active: '✅ Actif',
      inactive: '⚠️ Inactif',
      dead: '❌ Mort',
      not_configured: '⚙️ Non configuré',
      no_messages: '📭 Aucun message',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.not_configured}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getApiStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      ok: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      timeout: 'bg-yellow-100 text-yellow-800',
      unknown: 'bg-gray-100 text-gray-800',
    };
    const labels: Record<string, string> = {
      ok: '✅ OK',
      error: '❌ Erreur',
      timeout: '⏱️ Timeout',
      unknown: '❓ Inconnu',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.unknown}`}>
        {labels[status] || status}
      </span>
    );
  };

  const formatTimeAgo = (timestamp?: string) => {
    if (!timestamp) return 'Jamais';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffHours < 24) return `Il y a ${diffHours} h`;
    return `Il y a ${diffDays} j`;
  };

  if (loading) return <div className="text-gray-400 text-sm">Chargement des statistiques…</div>;

  const configuredCount = webhookStats.filter(s => s.configured).length;
  const activeCount = webhookStats.filter(s => s.status === 'active').length;
  const totalIncoming = webhookStats.reduce((sum, s) => sum + s.messages_incoming_24h, 0);
  const totalOutgoing = webhookStats.reduce((sum, s) => sum + s.messages_outgoing_24h, 0);
  const totalFailed = webhookStats.reduce((sum, s) => sum + s.messages_failed_24h, 0);

  const totalPerfIncoming = performanceStats.reduce((sum, s) => sum + s.total_messages_incoming, 0);
  const totalPerfOutgoing = performanceStats.reduce((sum, s) => sum + s.total_messages_outgoing, 0);
  const totalPerfFailed = performanceStats.reduce((sum, s) => sum + s.total_messages_failed, 0);
  const totalContacts = performanceStats.reduce((sum, s) => sum + s.total_contacts, 0);
  const totalNewContacts = performanceStats.reduce((sum, s) => sum + s.new_contacts_period, 0);
  const avgSuccessRate = performanceStats.length > 0 
    ? performanceStats.reduce((sum, s) => sum + s.success_rate, 0) / performanceStats.length 
    : 0;

  // Aggregate daily stats across all companies for the chart
  const aggregatedDailyStats = performanceStats.length > 0 
    ? performanceStats[0].daily_stats.map((day, index) => {
        const aggregated = {
          date: new Date(day.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
          incoming: 0,
          outgoing: 0,
          failed: 0,
          newContacts: 0
        };
        performanceStats.forEach(company => {
          if (company.daily_stats[index]) {
            aggregated.incoming += company.daily_stats[index].incoming;
            aggregated.outgoing += company.daily_stats[index].outgoing;
            aggregated.failed += company.daily_stats[index].failed;
            aggregated.newContacts += company.daily_stats[index].new_contacts || 0;
          }
        });
        return aggregated;
      })
    : [];

  return (
    <div className="max-w-7xl space-y-6 bg-white rounded-xl p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">📊 Dashboard WhatsApp Multi-Tenant</h1>
          <p className="text-sm text-gray-500">
            Monitoring et analytics pour toutes les entreprises
          </p>
        </div>
        <button 
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {refreshing ? '⏳' : '🔄'} Rafraîchir
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('webhooks')}
            className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'webhooks'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            📊 Webhooks
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'performance'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            📈 Performance
          </button>
        </nav>
      </div>

      {/* Webhooks Tab */}
      {activeTab === 'webhooks' && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Entreprises</p>
              <p className="text-2xl font-bold text-gray-900">{webhookStats.length}</p>
              <p className="text-xs text-green-600">{configuredCount} configurées</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Webhooks Actifs</p>
              <p className="text-2xl font-bold text-green-600">{activeCount}</p>
              <p className="text-xs text-gray-500">Messages &lt; 5 min</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Messages Entrants</p>
              <p className="text-2xl font-bold text-blue-600">{totalIncoming}</p>
              <p className="text-xs text-gray-500">24 dernières heures</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Messages Sortants</p>
              <p className="text-2xl font-bold text-indigo-600">{totalOutgoing}</p>
              <p className="text-xs text-gray-500">24 dernières heures</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Échecs</p>
              <p className="text-2xl font-bold text-red-600">{totalFailed}</p>
              <p className="text-xs text-gray-500">24 dernières heures</p>
            </div>
          </div>

          {/* Stats Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
              <h2 className="font-semibold text-gray-900">État par Entreprise</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {['Entreprise', 'État Webhook', 'API Meta', 'Messages (24h)', 'Dernier Réception', 'URL Webhook'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {webhookStats.map(stat => (
                    <tr key={stat.company_id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <p className="text-sm font-medium text-gray-900">{stat.company_name}</p>
                        <p className="text-xs text-gray-500 font-mono">{stat.company_id.slice(0, 8)}...</p>
                      </td>
                      <td className="px-4 py-4">
                        {getStatusBadge(stat.status)}
                      </td>
                      <td className="px-4 py-4">
                        {getApiStatusBadge(stat.api_connection_status)}
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex gap-2 text-xs">
                          <span className="bg-blue-50 text-blue-700 px- py-1 rounded">↘️ {stat.messages_incoming_24h}</span>
                          <span className="bg-indigo-50 text-indigo-700 px- py-1 rounded">↗️ {stat.messages_outgoing_24h}</span>
                          {stat.messages_failed_24h > 0 && (
                            <span className="bg-red-50 text-red-700 px- py-1 rounded">❌ {stat.messages_failed_24h}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-xs text-gray-600">
                        {formatTimeAgo(stat.last_message_received)}
                      </td>
                      <td className="px-4 py-4">
                        {stat.webhook_url ? (
                          <code className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
                            {stat.webhook_url.slice(0, 40)}...
                          </code>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Legend */}
          <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
            <h3 className="font-semibold text-gray-900 text-sm mb-3">Légende des États</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-gray-600"><strong>Actif:</strong> Messages &lt; 5 min</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="text-gray-600"><strong>Inactif:</strong> 5-30 min</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="text-gray-600"><strong>Mort:</strong> &gt; 30 min</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gray-400"></span>
                <span className="text-gray-600"><strong>Aucun message:</strong> Jamais reçu</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gray-300"></span>
                <span className="text-gray-600"><strong>Non configuré:</strong> Pas de channel</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <>
          {/* Period Selector */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">Période :</span>
            <div className="flex gap-2">
              {[7, 30, 90].map(d => (
                <button
                  key={d}
                  onClick={() => setDaysPeriod(d)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium ${
                    daysPeriod === d
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {d}j
                </button>
              ))}
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Messages Entrants</p>
              <p className="text-2xl font-bold text-blue-600">{totalPerfIncoming}</p>
              <p className="text-xs text-gray-500">Derniers {daysPeriod} jours</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Messages Sortants</p>
              <p className="text-2xl font-bold text-indigo-600">{totalPerfOutgoing}</p>
              <p className="text-xs text-gray-500">Derniers {daysPeriod} jours</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Échecs</p>
              <p className="text-2xl font-bold text-red-600">{totalPerfFailed}</p>
              <p className="text-xs text-gray-500">Derniers {daysPeriod} jours</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Contacts Totaux</p>
              <p className="text-2xl font-bold text-purple-600">{totalContacts}</p>
              <p className="text-xs text-gray-500">Base de contacts</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Nouveaux Contacts</p>
              <p className="text-2xl font-bold text-green-600">{totalNewContacts}</p>
              <p className="text-xs text-gray-500">Derniers {daysPeriod} jours</p>
            </div>
          </div>

          {/* Secondary KPIs */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Taux de Succès</p>
              <p className="text-2xl font-bold text-green-600">{avgSuccessRate.toFixed(1)}%</p>
              <p className="text-xs text-gray-500">Moyenne global</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Entreprises</p>
              <p className="text-2xl font-bold text-gray-900">{performanceStats.length}</p>
              <p className="text-xs text-gray-500">Avec données</p>
            </div>
          </div>

          {/* Performance Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
              <h2 className="font-semibold text-gray-900">Performance par Entreprise</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {['Entreprise', 'Entrants', 'Sortants', 'Échecs', 'Taux Succès', 'Contacts Totaux', 'Nouveaux Contacts', 'Temps Réponse Moy'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {performanceStats.map(stat => (
                    <tr key={stat.company_id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <p className="text-sm font-medium text-gray-900">{stat.company_name}</p>
                        <p className="text-xs text-gray-500 font-mono">{stat.company_id.slice(0, 8)}...</p>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm font-semibold text-blue-600">{stat.total_messages_incoming}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm font-semibold text-indigo-600">{stat.total_messages_outgoing}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`text-sm font-semibold ${stat.total_messages_failed > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {stat.total_messages_failed}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`text-sm font-semibold ${stat.success_rate >= 95 ? 'text-green-600' : stat.success_rate >= 80 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {stat.success_rate.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm font-semibold text-purple-600">{stat.total_contacts}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`text-sm font-semibold ${stat.new_contacts_period > 0 ? 'text-green-600' : 'text-gray-400'}`}>
                          +{stat.new_contacts_period}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        {stat.avg_response_time_seconds ? (
                          <span className="text-sm text-gray-600">{stat.avg_response_time_seconds.toFixed(1)}s</span>
                        ) : (
                          <span className="text-sm text-gray-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Daily Trend Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-900 mb-4">📈 Évolution Quotidienne</h2>
            
            {/* Chart Type Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setChartType('line')}
                className={`px-3 py-1 rounded-lg text-sm font-medium ${
                  chartType === 'line'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Ligne
              </button>
              <button
                onClick={() => setChartType('bar')}
                className={`px-3 py-1 rounded-lg text-sm font-medium ${
                  chartType === 'bar'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Barres
              </button>
            </div>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                {chartType === 'line' ? (
                  <LineChart data={aggregatedDailyStats}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="incoming" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      name="Messages Entrants"
                      dot={{ r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="outgoing" 
                      stroke="#6366f1" 
                      strokeWidth={2}
                      name="Messages Sortants"
                      dot={{ r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="newContacts" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      name="Nouveaux Contacts"
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                ) : (
                  <BarChart data={aggregatedDailyStats}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="incoming" fill="#3b82f6" name="Messages Entrants" />
                    <Bar dataKey="outgoing" fill="#6366f1" name="Messages Sortants" />
                    <Bar dataKey="newContacts" fill="#10b981" name="Nouveaux Contacts" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function WhatsAppPage() {
  const { user } = useAuth();

  if (user?.role === 'SUPER_ADMIN') {
    return (
      <AppLayout>
        <SuperAdminWebhookPanel />
      </AppLayout>
    );
  }

  const [messages, setMessages]   = useState<WhatsAppMessage[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [credentials, setCredentials] = useState<WACredentials | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [success, setSuccess]     = useState('');
  const [activeTab, setActiveTab] = useHashTab<'connexion' | 'messages' | 'templates'>('connexion');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleting, setDeleting]   = useState(false);
  const [conversationPhone, setConversationPhone] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [credForm, setCredForm]   = useState({ 
    phone_number_id: '', access_token: '', waba_id: '', display_phone_number: '',
    meta_app_id: '', meta_app_secret: '', meta_business_id: '', webhook_verify_token: ''
  });

  useEffect(() => {
    if (user) {
      fetchCredentials();
      fetchMessages();
      fetchTemplates();
    }
  }, [user]);

  const fetchCredentials = async () => {
    try {
      const r = await api.get('/whatsapp/config');
      setCredentials(r.data);
      if (r.data.configured) {
        setCredForm(f => ({ 
          ...f, 
          phone_number_id: r.data.phone_number_id || '', 
          waba_id: r.data.waba_id || '', 
          display_phone_number: r.data.display_phone_number || '',
          meta_app_id: r.data.meta_app_id || '',
          meta_business_id: r.data.meta_business_id || '',
          // Pre-fill with masked values (user can overwrite)
          access_token: r.data.access_token_masked || '',
          meta_app_secret: r.data.meta_app_secret_masked || '',
          webhook_verify_token: r.data.webhook_verify_token_masked || ''
        }));
      }
    } catch {} finally { setLoading(false); }
  };

  const saveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const r = await api.put('/whatsapp/config', {
        phone_number_id: credForm.phone_number_id || undefined,
        access_token: credForm.access_token || undefined,
        meta_app_id: credForm.meta_app_id || undefined,
        meta_app_secret: credForm.meta_app_secret || undefined,
        meta_business_id: credForm.meta_business_id || undefined,
        webhook_verify_token: credForm.webhook_verify_token || undefined
      });
      setSuccess('Configuration WhatsApp enregistrée !');
      fetchCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur sauvegarde');
    } finally { setSubmitting(false); }
  };

  const fetchMessages = async () => {
    try {
      const response = await api.get('/whatsapp/messages', { params: { limit: 500 } });
      setMessages(response.data.messages);
      setTotalMessages(response.data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch messages');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await api.get('/whatsapp/templates/active');
      setTemplates(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch templates');
    }
  };

  const toggleSelectMessage = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleSelectAllMessages = () => {
    setSelectedIds(prev => prev.size === messages.length ? new Set() : new Set(messages.map(m => m.id)));
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Supprimer ${selectedIds.size} message(s) ? Cette action est irréversible.`)) return;
    setDeleting(true);
    try {
      await api.delete('/whatsapp/messages', { data: { message_ids: Array.from(selectedIds) } });
      setSelectedIds(new Set());
      setSuccess('Message(s) supprimé(s) !');
      fetchMessages();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression');
    } finally {
      setDeleting(false);
    }
  };

  const [showSendModal, setShowSendModal] = useState(false);
  const [sendForm, setSendForm] = useState({ phone_number: '', content: '' });

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/whatsapp/messages/send', sendForm);
      setSuccess('Message envoyé !');
      setShowSendModal(false);
      setSendForm({ phone_number: '', content: '' });
      fetchMessages();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur envoi');
    } finally { setSubmitting(false); }
  };

  if (loading) return (
    <AppLayout><div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div></AppLayout>
  );

  const TABS = [
    { key: 'connexion', label: credentials?.configured ? '✅ Connexion' : '🔌 Connexion' },
    { key: 'messages',  label: `💬 Messages (${totalMessages})` },
    { key: 'templates', label: '📋 Templates' },
  ] as const;

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">📱 WhatsApp</h1>
          {credentials?.configured && (
            <button onClick={() => setShowSendModal(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
              + Envoyer un message
            </button>
          )}
        </div>

        {error && <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm"><span>{error}</span><button onClick={() => setError('')}>✕</button></div>}
        {success && <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm"><span>✅ {success}</span><button onClick={() => setSuccess('')}>✕</button></div>}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {TABS.map(tab => (
              <button key={tab.key} onClick={() => setActiveTab(tab.key as any)}
                className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key ? 'border-green-500 text-green-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* ── CONNEXION ── */}
        {activeTab === 'connexion' && (
          <div className="max-w-xl space-y-6">

            {/* Statut connexion actuelle */}
            {credentials?.configured && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
                <span className="text-2xl">✅</span>
                <div className="flex-1">
                  <p className="font-semibold text-green-800 text-sm">WhatsApp configuré</p>
                  <p className="text-xs text-green-700 mt-0.5">Numéro : <span className="font-mono">{credentials.display_phone_number || '—'}</span></p>
                  <p className="text-xs text-green-700">Phone Number ID : <span className="font-mono">{credentials.phone_number_id}</span></p>
                  <p className="text-xs text-green-700">Meta App ID : <span className="font-mono">{credentials.meta_app_id || '—'}</span></p>
                  <p className="text-xs text-green-700">Meta Business ID : <span className="font-mono">{credentials.meta_business_id || '—'}</span></p>
                  <p className="text-xs text-green-700">Token : <span className="font-mono">{credentials.access_token_masked}</span></p>
                  {credentials.webhook_url && (
                    <p className="text-xs text-green-700 mt-2">Webhook URL : <span className="font-mono text-xs">{credentials.webhook_url}</span></p>
                  )}
                </div>
              </div>
            )}

            {/* ── Configuration manuelle (Multi-tenant) ── */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-semibold text-gray-900 mb-1">✏️ Configuration manuelle (Multi-tenant)</h2>
              <p className="text-xs text-gray-500 mb-5">
                Configurez vos propres identifiants Meta pour votre entreprise. Chaque tenant a sa propre configuration.
              </p>
              <form onSubmit={saveCredentials} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Meta App ID <span className="text-red-500">*</span></label>
                    <input value={credForm.meta_app_id}
                      onChange={e => setCredForm({...credForm, meta_app_id: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                      placeholder="1512138164296574" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Meta Business ID <span className="text-red-500">*</span></label>
                    <input value={credForm.meta_business_id}
                      onChange={e => setCredForm({...credForm, meta_business_id: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                      placeholder="232803093077664" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Meta App Secret <span className="text-red-500">*</span></label>
                  <input type="password" value={credForm.meta_app_secret}
                    onChange={e => setCredForm({...credForm, meta_app_secret: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                    placeholder="22bc8b15890777fc545593241396fb46" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number ID <span className="text-red-500">*</span></label>
                  <input required value={credForm.phone_number_id}
                    onChange={e => setCredForm({...credForm, phone_number_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                    placeholder="122970883552303" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Access Token (Permanent) <span className="text-red-500">*</span></label>
                  <input required type="password" value={credForm.access_token}
                    onChange={e => setCredForm({...credForm, access_token: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                    placeholder="EAAxxxxxxxxx..." />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">WABA ID <span className="text-gray-400 font-normal">(optionnel)</span></label>
                  <input value={credForm.waba_id}
                    onChange={e => setCredForm({...credForm, waba_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                    placeholder="851253647787120" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Numéro affiché <span className="text-gray-400 font-normal">(optionnel)</span></label>
                  <input value={credForm.display_phone_number}
                    onChange={e => setCredForm({...credForm, display_phone_number: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    placeholder="+237 6 12 34 56 78" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Webhook Verify Token <span className="text-gray-400 font-normal">(optionnel)</span></label>
                  <input value={credForm.webhook_verify_token}
                    onChange={e => setCredForm({...credForm, webhook_verify_token: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                    placeholder="verify_token_123" />
                  <p className="text-xs text-gray-500 mt-1">Token pour valider le webhook sur Meta</p>
                </div>
                <button type="submit" disabled={submitting}
                  className="w-full bg-green-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50">
                  {submitting ? 'Enregistrement...' : credentials?.configured ? '💾 Mettre à jour' : '💾 Enregistrer'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Messages Tab */}
        {activeTab === 'messages' && (
          <div className="bg-white shadow rounded-xl overflow-hidden">
            {selectedIds.size > 0 && (
              <div className="bg-red-50 border-b border-red-200 px-5 py-3 flex items-center justify-between">
                <span className="text-sm text-red-700 font-medium">{selectedIds.size} message(s) sélectionné(s)</span>
                <div className="flex gap-2">
                  <button onClick={() => setSelectedIds(new Set())}
                    className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">Annuler</button>
                  <button onClick={handleDeleteSelected} disabled={deleting}
                    className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">
                    {deleting ? 'Suppression...' : '🗑️ Supprimer'}
                  </button>
                </div>
              </div>
            )}
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-5 py-3 w-10">
                    <input type="checkbox"
                      checked={messages.length > 0 && selectedIds.size === messages.length}
                      onChange={toggleSelectAllMessages}
                      className="rounded border-gray-300" />
                  </th>
                  {['Téléphone', 'Direction', 'Contenu', 'Statut', 'Date'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {messages.map(msg => (
                  <tr key={msg.id} className={`hover:bg-gray-50 cursor-pointer ${selectedIds.has(msg.id) ? 'bg-green-50' : ''}`}
                    onClick={() => setConversationPhone(msg.phone_number)}>
                    <td className="px-5 py-4" onClick={e => e.stopPropagation()}>
                      <input type="checkbox" checked={selectedIds.has(msg.id)}
                        onChange={() => toggleSelectMessage(msg.id)}
                        className="rounded border-gray-300" />
                    </td>
                    <td className="px-5 py-4">
                      <p className="text-sm font-medium text-gray-900">{msg.phone_number}</p>
                      {msg.display_name && <p className="text-xs text-gray-500">{msg.display_name}</p>}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        msg.direction === 'OUTGOING' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {msg.direction === 'OUTGOING' ? '↗️ Sortant' : '↘️ Entrant'}
                      </span>
                    </td>
                    <td className="px-5 py-4 max-w-xs">
                      <p className="text-sm text-gray-700 truncate">{msg.content || '(média)'}</p>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        msg.status === 'DELIVERED' || msg.status === 'READ' ? 'bg-green-100 text-green-700' :
                        msg.status === 'FAILED' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>{msg.status}</span>
                    </td>
                    <td className="px-5 py-4 text-xs text-gray-500">
                      {new Date(msg.created_at).toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {messages.length === 0 && (
              <div className="text-center py-12 text-gray-400 text-sm">Aucun message</div>
            )}
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div className="bg-white shadow rounded-xl overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['Nom', 'Catégorie', 'Langue', 'Statut'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {templates.map(t => (
                  <tr key={t.id} className="hover:bg-gray-50">
                    <td className="px-5 py-4 text-sm font-medium text-gray-900">{t.name}</td>
                    <td className="px-5 py-4 text-sm text-gray-500">{t.category}</td>
                    <td className="px-5 py-4 text-sm text-gray-500">{t.language}</td>
                    <td className="px-5 py-4">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        t.is_approved ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>{t.is_approved ? '✅ Approuvé' : '⏳ En attente'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {templates.length === 0 && (
              <div className="text-center py-12 text-gray-400 text-sm">Aucun template</div>
            )}
          </div>
        )}
      </div>

      {/* Modal Envoi */}
      {showSendModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">📱 Envoyer un message WhatsApp</h3>
            <form onSubmit={handleSendMessage} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Numéro de téléphone *</label>
                <input required type="tel" value={sendForm.phone_number}
                  onChange={e => setSendForm({...sendForm, phone_number: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                  placeholder="+33612345678" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Message *</label>
                <textarea required value={sendForm.content}
                  onChange={e => setSendForm({...sendForm, content: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500"
                  rows={4} placeholder="Votre message..." />
              </div>
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowSendModal(false)}
                  className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
                <button type="submit" disabled={submitting}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">
                  {submitting ? 'Envoi...' : 'Envoyer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Conversation */}
      {conversationPhone && (
        <ConversationModal
          phoneNumber={conversationPhone}
          onClose={() => setConversationPhone(null)}
        />
      )}
    </AppLayout>
  );
}

function ConversationModal({ phoneNumber, onClose }: { phoneNumber: string; onClose: () => void }) {
  const [convMessages, setConvMessages] = useState<WhatsAppMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get('/whatsapp/messages', { params: { phone_number: phoneNumber, limit: 500 } });
        if (!cancelled) {
          const msgs: WhatsAppMessage[] = r.data.messages || [];
          // Oldest first, to read the conversation top to bottom
          msgs.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
          setConvMessages(msgs);
        }
      } catch (err: any) {
        if (!cancelled) setError(err.response?.data?.detail || 'Erreur chargement conversation');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [phoneNumber]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl w-full max-w-lg shadow-xl flex flex-col max-h-[80vh]" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div>
            <h3 className="font-bold text-gray-900">💬 Conversation</h3>
            <p className="text-xs text-gray-500 font-mono">{phoneNumber}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3 bg-gray-50">
          {loading && <div className="text-center text-gray-400 text-sm py-8">Chargement...</div>}
          {error && <div className="text-center text-red-500 text-sm py-8">{error}</div>}
          {!loading && !error && convMessages.length === 0 && (
            <div className="text-center text-gray-400 text-sm py-8">Aucun message</div>
          )}
          {!loading && !error && convMessages.map(msg => (
            <div key={msg.id} className={`flex ${msg.direction === 'OUTGOING' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
                msg.direction === 'OUTGOING' ? 'bg-green-600 text-white' : 'bg-white border border-gray-200 text-gray-800'
              }`}>
                <p className="whitespace-pre-wrap break-words">{msg.content || '(média)'}</p>
                <p className={`text-[10px] mt-1 ${msg.direction === 'OUTGOING' ? 'text-green-100' : 'text-gray-400'}`}>
                  {new Date(msg.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  {' · '}{msg.status}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
