'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../hooks/useAuth';
import AppLayout from '../../components/AppLayout';
import api from '../../lib/api';
import Link from 'next/link';

interface Company {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  is_suspended: boolean;
  created_at: string;
}

interface ConvItem {
  id: string;
  status: string;
  priority: string;
  assigned_agent_id: string | null;
  customer_id: string;
  last_activity_at: string;
  created_at: string;
}

interface CustomerItem {
  id: string;
  name: string | null;
  phone_number: string;
  last_seen_at: string;
  created_at: string;
}

interface AgentItem {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  is_active: boolean;
}

interface Stats {
  companies_total?: number;
  companies_active?: number;
  companies_suspended?: number;
  companies_this_month?: number;
  users?: number;
  agents_active?: number;
  conv_open?: number;
  conv_waiting?: number;
  conv_closed?: number;
  customers_total?: number;
  assigned_to_me?: number;
  unassigned?: number;
}

export default function Dashboard() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [stats, setStats]                           = useState<Stats>({});
  const [suspendedCompanies, setSuspendedCompanies] = useState<Company[]>([]);
  const [recentCompanies, setRecentCompanies]       = useState<Company[]>([]);
  const [recentUsers, setRecentUsers]               = useState<any[]>([]);
  const [recentConvs, setRecentConvs]               = useState<ConvItem[]>([]);
  const [urgentConvs, setUrgentConvs]               = useState<ConvItem[]>([]);
  const [waitingConvs, setWaitingConvs]             = useState<ConvItem[]>([]);
  const [agents, setAgents]                         = useState<AgentItem[]>([]);
  const [customerMap, setCustomerMap]               = useState<Record<string, CustomerItem>>({});
  const [recentCustomers, setRecentCustomers]       = useState<CustomerItem[]>([]);
  const [assigningId, setAssigningId]               = useState<string | null>(null);
  const [selectAgent, setSelectAgent]               = useState<Record<string, string>>({});

  useEffect(() => {
    if (!loading && !user) router.push('/auth/login');
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;

    if (user.role === 'SUPER_ADMIN') {
      Promise.allSettled([
        api.get('/companies/'),
        api.get('/users/'),
      ]).then(([co, us]) => {
        if (co.status === 'fulfilled') {
          const all: Company[] = co.value.data;
          const now = new Date();
          const firstOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
          setSuspendedCompanies(all.filter(c => c.is_suspended));
          setRecentCompanies([...all].sort((a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          ).slice(0, 5));
          setStats(prev => ({
            ...prev,
            companies_total:      all.length,
            companies_active:     all.filter(c => c.is_active && !c.is_suspended).length,
            companies_suspended:  all.filter(c => c.is_suspended).length,
            companies_this_month: all.filter(c => new Date(c.created_at) >= firstOfMonth).length,
            users: us.status === 'fulfilled' ? us.value.data.length : undefined,
          }));
        }
        if (us.status === 'fulfilled') {
          setRecentUsers([...us.value.data].sort((a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          ).slice(0, 5));
        }
      });
    } else {
      Promise.allSettled([
        api.get('/users/'),
        api.get('/conversations/conversations'),
        api.get('/customers/'),
        api.get('/conversations/stats'),
      ]).then(([us, cv, cu, st]) => {
        const users: AgentItem[]   = us.status === 'fulfilled' ? us.value.data : [];
        const cvData = cv.status === 'fulfilled' ? cv.value.data : {};
        const convs: ConvItem[] = Array.isArray(cvData) ? cvData : (cvData.conversations || []);
        const convTotal: number = cvData.total ?? convs.length;
        const cuData = cu.status === 'fulfilled' ? cu.value.data : {};
        const customers: CustomerItem[] = Array.isArray(cuData) ? cuData : (cuData.customers || []);
        const custTotal: number = cuData.total ?? customers.length;
        const convStats = st.status === 'fulfilled' ? st.value.data : {};

        const now = new Date();
        const staleThreshold = new Date(now.getTime() - 2 * 60 * 60 * 1000);

        const activeAgents = users.filter(u => (u.role === 'AGENT' || u.role === 'COMPANY_ADMIN') && u.is_active);
        setAgents(activeAgents);

        const cMap: Record<string, CustomerItem> = {};
        customers.forEach(c => { cMap[c.id] = c; });
        setCustomerMap(cMap);

        setStats({
          users:           users.length,
          agents_active:   users.filter((u: any) => u.role === 'AGENT' && u.is_active).length,
          conv_open:       convStats.by_status?.OPEN || 0,
          conv_waiting:    convStats.by_status?.WAITING || 0,
          conv_closed:     convStats.by_status?.CLOSED || 0,
          customers_total: custTotal,
          assigned_to_me:  convStats.assigned_to_me || 0,
          unassigned:      convStats.unassigned || 0,
        });

        const waiting = convs
          .filter(c => c.status === 'WAITING')
          .sort((a, b) => new Date(a.last_activity_at).getTime() - new Date(b.last_activity_at).getTime());
        setWaitingConvs(waiting);

        setUrgentConvs(
          waiting
            .filter(c => new Date(c.last_activity_at) < staleThreshold)
            .slice(0, 5)
        );

        setRecentConvs(
          [...convs]
            .filter(c => c.status !== 'CLOSED' && c.status !== 'ARCHIVED')
            .sort((a, b) => new Date(b.last_activity_at).getTime() - new Date(a.last_activity_at).getTime())
            .slice(0, 5)
        );

        setRecentCustomers(
          [...customers]
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, 5)
        );
      });
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  const roleLabel =
    user.role === 'SUPER_ADMIN'   ? 'Super Admin'     :
    user.role === 'COMPANY_ADMIN' ? 'Admin Entreprise' : 'Agent';

  const AGENT_CARDS = [
    { href: '/conversations', icon: '✋', label: 'Assignées à moi',   count: stats.assigned_to_me,  color: 'bg-green-50 dark:bg-green-900/30 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300',  highlight: (stats.assigned_to_me || 0) > 0 },
    { href: '/conversations', icon: '⏳', label: 'En attente',        count: stats.conv_waiting,    color: 'bg-amber-50 dark:bg-amber-900/30 border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300',  highlight: (stats.conv_waiting || 0) > 0 },
    { href: '/conversations', icon: '�', label: 'Non assignées',     count: stats.unassigned,      color: 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-700 text-red-700 dark:text-red-300',        highlight: (stats.unassigned || 0) > 0 },
    { href: '/conversations', icon: '💬', label: 'Ouvertes total',    count: stats.conv_open,       color: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300',     highlight: false },
    { href: '/conversations', icon: '✅', label: 'Clôturées',         count: stats.conv_closed,     color: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300',     highlight: false },
    { href: '/customers',     icon: '👤', label: 'Clients',           count: stats.customers_total, color: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300', highlight: false },
  ];

  const STATUS_COLORS: Record<string, string> = {
    OPEN:    'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200',
    WAITING: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-200',
    AI:      'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200',
    AGENT:   'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200',
    CLOSED:  'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-100',
  };

  const timeAgo = (date: string) => {
    const diff = Math.floor((Date.now() - new Date(date).getTime()) / 60000);
    if (diff < 60) return `${diff}min`;
    if (diff < 1440) return `${Math.floor(diff/60)}h`;
    return `${Math.floor(diff/1440)}j`;
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Bonjour, {user.first_name} 👋</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Connecté en tant que <span className="font-medium text-green-600 dark:text-green-400">{roleLabel}</span>
          </p>
        </div>

        {/* ── SUPER ADMIN ── */}
        {user.role === 'SUPER_ADMIN' && (
          <>
            {/* Stats cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Entreprises total',     value: stats.companies_total,     icon: '🏢', color: 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300' },
                { label: 'Actives',               value: stats.companies_active,    icon: '✅', color: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300' },
                { label: 'Suspendues',            value: stats.companies_suspended, icon: '⛔', color: stats.companies_suspended ? 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-700 text-red-700 dark:text-red-300' : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400' },
                { label: 'Créées ce mois',        value: stats.companies_this_month,icon: '📅', color: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300' },
              ].map(c => (
                <div key={c.label} className={`rounded-xl border-2 p-5 ${c.color}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{c.icon}</span>
                    {c.value !== undefined && (
                      <span className="text-3xl font-bold">{c.value}</span>
                    )}
                  </div>
                  <p className="text-sm font-medium opacity-75">{c.label}</p>
                </div>
              ))}
            </div>

            {/* Utilisateurs */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="rounded-xl border-2 bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300 p-5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl">👥</span>
                  {stats.users !== undefined && <span className="text-3xl font-bold">{stats.users}</span>}
                </div>
                <p className="text-sm font-medium opacity-75">Utilisateurs total</p>
              </div>
            </div>

            {/* Actions rapides */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-4">⚡ Actions rapides</h2>
              <div className="flex flex-wrap gap-3">
                <Link href="/companies" className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm font-medium">
                  + Nouvelle entreprise
                </Link>
                <Link href="/users" className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm font-medium">
                  + Nouvel utilisateur
                </Link>
              </div>
            </div>

            {/* Alertes : entreprises suspendues */}
            {suspendedCompanies.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl p-6">
                <h2 className="text-base font-semibold text-red-700 dark:text-red-300 mb-4">
                  🚨 Entreprises suspendues ({suspendedCompanies.length})
                </h2>
                <div className="space-y-2">
                  {suspendedCompanies.map(c => (
                    <div key={c.id} className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg px-4 py-2 border border-red-100 dark:border-red-900">
                      <div>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">{c.name}</span>
                        <span className="text-xs text-gray-400 ml-2">{c.slug}</span>
                      </div>
                      <Link href="/companies" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-medium">
                        Gérer →
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Récents */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Dernières entreprises */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">🏢 Dernières entreprises</h2>
                  <Link href="/companies" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Voir tout</Link>
                </div>
                <div className="space-y-3">
                  {recentCompanies.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-4">Aucune entreprise</p>
                  ) : recentCompanies.map(c => (
                    <div key={c.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm">
                          {c.name[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{c.name}</p>
                          <p className="text-xs text-gray-400">{new Date(c.created_at).toLocaleDateString('fr-FR')}</p>
                        </div>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        c.is_suspended ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300' :
                        c.is_active    ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400'
                      }`}>
                        {c.is_suspended ? 'Suspendue' : c.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Derniers utilisateurs */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">👥 Derniers utilisateurs</h2>
                  <Link href="/users" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Voir tout</Link>
                </div>
                <div className="space-y-3">
                  {recentUsers.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-4">Aucun utilisateur</p>
                  ) : recentUsers.map(u => (
                    <div key={u.id} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center text-purple-600 dark:text-purple-400 font-bold text-sm">
                        {(u.first_name || u.email)[0].toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {u.first_name} {u.last_name}
                        </p>
                        <p className="text-xs text-gray-400 truncate">{u.email}</p>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${
                        u.role === 'SUPER_ADMIN'   ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300' :
                        u.role === 'COMPANY_ADMIN' ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300' :
                        'bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-300'
                      }`}>
                        {u.role === 'SUPER_ADMIN' ? 'Super Admin' : u.role === 'COMPANY_ADMIN' ? 'Admin' : 'Agent'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {/* ── WAITING alert banner (COMPANY_ADMIN + AGENT) ── */}
        {(user.role === 'COMPANY_ADMIN' || user.role === 'AGENT') && waitingConvs.length > 0 && (
          <div className="animate-pulse bg-amber-50 dark:bg-amber-900/30 border-2 border-amber-400 dark:border-amber-600 rounded-xl px-5 py-3 flex items-center justify-between gap-3">
            <span className="text-amber-800 dark:text-amber-200 font-semibold text-sm">
              🔔 <strong>{waitingConvs.length} conversation{waitingConvs.length > 1 ? 's' : ''}</strong> en attente d&apos;intervention humaine (transfert bot)
            </span>
            <Link href="/conversations?status=WAITING"
              className="text-xs bg-amber-500 text-white px-3 py-1.5 rounded-lg hover:bg-amber-600 whitespace-nowrap font-medium">
              Voir tout →
            </Link>
          </div>
        )}

        {/* ── COMPANY ADMIN ── */}
        {user.role === 'COMPANY_ADMIN' && (
          <>
            {/* Ligne 1 — stats conversations */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Conversations ouvertes', value: stats.conv_open,    icon: '💬', color: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300',   href: '/conversations' },
                { label: 'En attente',             value: stats.conv_waiting, icon: '⏳', color: 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-300', href: '/conversations' },
                { label: 'Fermées',                value: stats.conv_closed,  icon: '✅', color: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300',     href: '/conversations' },
                { label: 'Clients WhatsApp',       value: stats.customers_total, icon: '👤', color: 'bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800 text-orange-700 dark:text-orange-300', href: '/customers' },
              ].map(c => (
                <Link key={c.label} href={c.href} className={`rounded-xl border-2 p-5 hover:shadow-md transition-shadow ${c.color}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{c.icon}</span>
                    {c.value !== undefined && <span className="text-3xl font-bold">{c.value}</span>}
                  </div>
                  <p className="text-sm font-medium opacity-75">{c.label}</p>
                </Link>
              ))}
            </div>

            {/* Ligne 2 — stats équipe + accès rapides modules */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Membres équipe',        value: stats.users,         icon: '👥', color: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300', href: '/users' },
                { label: 'Agents actifs',          value: stats.agents_active, icon: '🟢', color: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300',   href: '/users' },
                { label: 'Chatbot',                value: undefined,           icon: '🤖', color: 'bg-teal-50 dark:bg-teal-900/30 border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300',      href: '/bot' },
                { label: 'Base de connaissances',  value: undefined,           icon: '📚', color: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300',   href: '/knowledge' },
              ].map(c => (
                <Link key={c.label} href={c.href} className={`rounded-xl border-2 p-5 hover:shadow-md transition-shadow ${c.color}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{c.icon}</span>
                    {c.value !== undefined
                      ? <span className="text-3xl font-bold">{c.value}</span>
                      : <span className="text-sm font-semibold opacity-60">Accéder →</span>
                    }
                  </div>
                  <p className="text-sm font-medium opacity-75">{c.label}</p>
                </Link>
              ))}
            </div>

            {/* Actions rapides */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100 mb-4">⚡ Actions rapides</h2>
              <div className="flex flex-wrap gap-3">
                <Link href="/users" className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm font-medium">
                  + Inviter un agent
                </Link>
                <Link href="/conversations" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium">
                  Voir conversations en attente
                </Link>
                <Link href="/bot" className="bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700 text-sm font-medium">
                  Configurer le bot
                </Link>
                <Link href="/whatsapp" className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm font-medium">
                  📱 WhatsApp
                </Link>
              </div>
            </div>

            {/* ── Section WAITING : transferts bot en attente d'agent ── */}
            {waitingConvs.length > 0 && (
              <div className="bg-amber-50 dark:bg-amber-900/30 border-2 border-amber-300 dark:border-amber-700 rounded-xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-semibold text-amber-800 dark:text-amber-200">
                    🔔 Transferts en attente d&apos;agent ({waitingConvs.length})
                  </h2>
                  <Link href="/conversations" className="text-xs text-amber-700 dark:text-amber-300 hover:underline font-medium">Voir dans conversations →</Link>
                </div>
                <div className="space-y-2">
                  {waitingConvs.slice(0, 8).map(c => {
                    const cust = customerMap[c.customer_id];
                    return (
                      <div key={c.id} className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg px-4 py-2.5 border border-amber-200 dark:border-amber-800 gap-3 flex-wrap">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center text-amber-700 dark:text-amber-300 font-bold text-xs flex-shrink-0">
                            {(cust?.name || cust?.phone_number || '?')[0].toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{cust?.name || cust?.phone_number || 'Client'}</p>
                            <p className="text-xs text-gray-400">{cust?.phone_number} · {timeAgo(c.last_activity_at)} sans réponse</p>
                          </div>
                          {!c.assigned_agent_id && (
                            <span className="text-xs bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 font-medium px-1.5 py-0.5 rounded-full flex-shrink-0">Non assignée</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {/* Prendre soi-même */}
                          <button
                            disabled={assigningId === c.id}
                            onClick={async () => {
                              setAssigningId(c.id);
                              try {
                                await api.post(`/conversations/conversations/${c.id}/take`);
                                setWaitingConvs(prev => prev.filter(x => x.id !== c.id));
                                setStats(prev => ({ ...prev, conv_waiting: (prev.conv_waiting || 1) - 1 }));
                              } catch {}
                              setAssigningId(null);
                            }}
                            className="text-xs bg-green-600 text-white px-2.5 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium">
                            ✋ Prendre
                          </button>
                          {/* Assigner à un agent */}
                          <select
                            value={selectAgent[c.id] || ''}
                            onChange={e => setSelectAgent(prev => ({ ...prev, [c.id]: e.target.value }))}
                            className="text-xs border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1.5 focus:ring-2 focus:ring-amber-400 bg-white dark:bg-gray-800">
                            <option value="">Assigner à…</option>
                            {agents.map(a => (
                              <option key={a.id} value={a.id}>{a.first_name} {a.last_name}</option>
                            ))}
                          </select>
                          {selectAgent[c.id] && (
                            <button
                              disabled={assigningId === c.id}
                              onClick={async () => {
                                const agentId = selectAgent[c.id];
                                if (!agentId) return;
                                setAssigningId(c.id);
                                try {
                                  await api.post(`/conversations/conversations/${c.id}/assign`, { agent_id: agentId });
                                  setWaitingConvs(prev => prev.filter(x => x.id !== c.id));
                                  setStats(prev => ({ ...prev, conv_waiting: (prev.conv_waiting || 1) - 1 }));
                                } catch {}
                                setAssigningId(null);
                              }}
                              className="text-xs bg-blue-600 text-white px-2.5 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
                              ✔ OK
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Activité récente : conversations + clients */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Conversations actives récentes */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">💬 Conversations actives</h2>
                  <Link href="/conversations" className="text-xs text-blue-600 dark:text-blue-400 hover:underline">Voir tout</Link>
                </div>
                <div className="space-y-3">
                  {recentConvs.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-4">Aucune conversation active</p>
                  ) : recentConvs.map(c => (
                    <Link key={c.id} href="/conversations"
                      className="flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg px-2 py-1 -mx-2 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400 text-xs font-bold">
                          💬
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">Client #{c.customer_id.slice(0, 8)}</p>
                          <p className="text-xs text-gray-400">{timeAgo(c.last_activity_at)} · {c.priority}</p>
                        </div>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_COLORS[c.status] || 'bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-300'}`}>
                        {c.status}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>

              {/* Derniers clients */}
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">👤 Nouveaux clients</h2>
                  <Link href="/customers" className="text-xs text-orange-600 dark:text-orange-400 hover:underline">Voir tout</Link>
                </div>
                <div className="space-y-3">
                  {recentCustomers.length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-4">Aucun client</p>
                  ) : recentCustomers.map(c => (
                    <div key={c.id} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-900/40 flex items-center justify-center text-orange-600 dark:text-orange-400 font-bold text-sm">
                        {(c.name || c.phone_number)[0].toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{c.name || 'Sans nom'}</p>
                        <p className="text-xs text-gray-400">{c.phone_number}</p>
                      </div>
                      <span className="text-xs text-gray-400">{timeAgo(c.created_at)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {/* ── AGENT / COMPANY_ADMIN ── */}
        {(user.role === 'AGENT' || user.role === 'COMPANY_ADMIN') && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {AGENT_CARDS.map((card, i) => (
              <Link key={i} href={card.href}
                className={`flex items-center gap-3 p-4 rounded-xl border-2 hover:shadow-md transition-all ${card.color} ${card.highlight ? 'ring-2 ring-offset-1 ring-current shadow-sm' : ''}`}>
                <span className="text-3xl">{card.icon}</span>
                <div className="min-w-0">
                  <p className="text-xs font-medium opacity-70 leading-tight">{card.label}</p>
                  {card.count !== undefined
                    ? <p className={`font-bold mt-0.5 ${card.highlight ? 'text-2xl' : 'text-xl'}`}>{card.count}</p>
                    : <p className="text-sm font-semibold mt-0.5">→</p>
                  }
                </div>
              </Link>
            ))}
          </div>
        )}

      </div>
    </AppLayout>
  );
}
