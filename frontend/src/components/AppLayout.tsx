'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';

const NAV_SUPER_ADMIN = [
  { href: '/dashboard',  label: 'Dashboard',    icon: '🏠' },
  { href: '/companies',  label: 'Entreprises',  icon: '🏢' },
  { href: '/users',      label: 'Utilisateurs', icon: '👥' },
  { href: '/whatsapp',   label: 'Webhook Meta', icon: '🔗' },
];

const NAV_COMPANY_ADMIN = [
  { href: '/dashboard',    label: 'Dashboard',          icon: '🏠' },
  { href: '/conversations',label: 'Conversations',       icon: '💬' },
  { href: '/customers',    label: 'Clients',             icon: '👤' },
  { href: '/bot',          label: 'Chatbot',             icon: '🤖' },
  { href: '/catalogue',    label: 'Catalogue',           icon: '🛍️' },
  { href: '/knowledge',    label: 'Base de connaissances',icon: '📚' },
  { href: '/users',        label: 'Équipe',              icon: '👥' },
  { href: '/whatsapp',     label: 'WhatsApp',            icon: '📱' },
];

const NAV_AGENT = [
  { href: '/dashboard',    label: 'Dashboard',    icon: '🏠' },
  { href: '/conversations',label: 'Conversations', icon: '💬' },
  { href: '/customers',    label: 'Clients',       icon: '👤' },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [convBadge, setConvBadge] = useState(0);

  useEffect(() => {
    if (!user || user.role === 'SUPER_ADMIN') return;
    const fetchBadge = async () => {
      try {
        const r = await api.get('/conversations/stats');
        const s = r.data.by_status || {};
        setConvBadge((s.OPEN || 0) + (s.WAITING || 0));
      } catch {}
    };
    fetchBadge();
    const iv = setInterval(fetchBadge, 30000);
    return () => clearInterval(iv);
  }, [user]);

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  const navItems =
    user?.role === 'SUPER_ADMIN'   ? NAV_SUPER_ADMIN  :
    user?.role === 'COMPANY_ADMIN' ? NAV_COMPANY_ADMIN :
    NAV_AGENT;

  const roleLabel =
    user?.role === 'SUPER_ADMIN'   ? 'Super Admin'    :
    user?.role === 'COMPANY_ADMIN' ? 'Admin Entreprise':
    'Agent';

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-gray-900 text-white flex flex-col transition-all duration-200`}>
        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-700">
          {sidebarOpen && (
            <span className="font-bold text-lg text-green-400">💬 {user?.company_name || 'ChatBot SaaS'}</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-400 hover:text-white ml-auto"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        {/* User info */}
        {sidebarOpen && (
          <div className="px-4 py-3 border-b border-gray-700">
            <p className="text-sm font-medium text-white">{user?.first_name} {user?.last_name}</p>
            <span className="text-xs bg-green-700 text-green-100 px-2 py-0.5 rounded-full">{roleLabel}</span>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = item.href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname === item.href || (pathname?.startsWith(item.href + '/') ?? false);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  active
                    ? 'bg-green-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <span className="text-base relative">
                  {item.icon}
                  {item.href === '/conversations' && convBadge > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center leading-none">
                      {convBadge > 9 ? '9+' : convBadge}
                    </span>
                  )}
                </span>
                {sidebarOpen && <span className="flex-1">{item.label}</span>}
                {sidebarOpen && item.href === '/conversations' && convBadge > 0 && (
                  <span className="bg-red-500 text-white text-xs font-bold rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
                    {convBadge > 99 ? '99+' : convBadge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="px-2 py-4 border-t border-gray-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm text-gray-300 hover:bg-red-700 hover:text-white transition-colors"
          >
            <span>🚪</span>
            {sidebarOpen && <span>Déconnexion</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white shadow-sm px-6 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-800">
            WhatsApp SaaS Platform
          </h1>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span>{user?.email}</span>
          </div>
        </header>

        {/* Page */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
