'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface Customer { id: string; phone_number: string; name: string | null; profile_picture_url: string | null; last_seen_at: string; }
interface Agent    { id: string; first_name: string; last_name: string; email: string; }
interface Conversation {
  id: string; company_id: string; customer_id: string; channel_id: string | null;
  status: string; priority: string; assigned_agent_id: string | null;
  tags: string[] | null; last_activity_at: string; created_at: string;
  _customer?: Customer; _last_message?: string;
}
interface Message {
  id: string; conversation_id: string; sender_type: string; sender_id: string | null;
  content: string | null; message_type: string; status: string; sent_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  OPEN: 'bg-green-100 text-green-700', WAITING: 'bg-amber-100 text-amber-700',
  AI: 'bg-purple-100 text-purple-700', AGENT: 'bg-blue-100 text-blue-700',
  CLOSED: 'bg-gray-100 text-gray-500', ARCHIVED: 'bg-red-100 text-red-600',
};
const PRIORITY_DOT: Record<string, string> = {
  LOW: 'bg-gray-400', MEDIUM: 'bg-blue-400', HIGH: 'bg-orange-400', URGENT: 'bg-red-500',
};
const STATUSES = ['OPEN','WAITING','AI','AGENT','CLOSED','ARCHIVED'];

function clientLabel(c?: Customer): string {
  if (!c) return '…';
  return c.name?.trim() || c.phone_number;
}

export default function ConversationsPage() {
  const { user } = useAuth();
  const [conversations, setConversations]   = useState<Conversation[]>([]);
  const [selected,      setSelectedRaw]     = useState<Conversation | null>(null);
  const pendingHashId = useRef<string | null>(typeof window !== 'undefined' ? window.location.hash.replace('#', '') || null : null);
  const [messages,      setMessages]        = useState<Message[]>([]);
  const [customers,     setCustomers]       = useState<Record<string, Customer>>({});
  const [agents,        setAgents]          = useState<Agent[]>([]);
  const [loading,       setLoading]         = useState(true);
  const [error,         setError]           = useState('');
  const [statusFilter,  setStatusFilter]    = useState('');
  const [searchQ,       setSearchQ]         = useState('');
  const [newMessage,    setNewMessage]      = useState('');
  const [sending,        setSending]         = useState(false);
  const [autoAssigning,   setAutoAssigning]   = useState(false);
  const [autoAssignMsg,   setAutoAssignMsg]   = useState('');
  const [showStatusModal,  setShowStatusModal]  = useState(false);
  const [showAssignModal,  setShowAssignModal]  = useState(false);
  const [showTagModal,     setShowTagModal]     = useState(false);
  const [modalStatus,  setModalStatus]  = useState('');
  const [modalAgentId, setModalAgentId] = useState('');
  const [modalTag,     setModalTag]     = useState('');
  const messagesEndRef   = useRef<HTMLDivElement>(null);
  const inputRef         = useRef<HTMLInputElement>(null);
  const prevSelectedId   = useRef<string | null>(null);
  const pollConvRef       = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAgents = useCallback(async () => {
    try { const r = await api.get('/users/'); setAgents(r.data); } catch {}
  }, []);

  const fetchCustomer = useCallback(async (cid: string) => {
    if (customers[cid]) return;
    try {
      const r = await api.get(`/conversations/customers/${cid}`);
      setCustomers(prev => ({ ...prev, [cid]: r.data }));
    } catch {}
  }, [customers]);

  // Wrap setSelected to also update the URL hash
  const setSelected = useCallback((convOrUpdater: Conversation | null | ((prev: Conversation | null) => Conversation | null)) => {
    if (typeof convOrUpdater === 'function') {
      setSelectedRaw(prev => {
        const next = convOrUpdater(prev);
        setTimeout(() => {
          window.history.replaceState(null, '', next ? `#${next.id}` : '#');
        }, 0);
        return next;
      });
    } else {
      setSelectedRaw(convOrUpdater);
      if (typeof window !== 'undefined') {
        window.history.replaceState(null, '', convOrUpdater ? `#${convOrUpdater.id}` : '#');
      }
    }
  }, []);

  const fetchConversations = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const res = await api.get(`/conversations/conversations${params}`, { params: { limit: 500 } });
      const rawData = res.data;
      const convs: Conversation[] = Array.isArray(rawData) ? rawData : (rawData.conversations || []);
      setConversations(prev => {
        if (!silent) return convs;
        // Silent merge: preserve order from server, update in place
        const prevMap = Object.fromEntries(prev.map(c => [c.id, c]));
        return convs.map(c => prevMap[c.id] ? { ...prevMap[c.id], ...c } : c);
      });
      // Sync selected conv status if it changed
      if (silent) {
        setSelected(prev => {
          if (!prev) return prev;
          const fresh = convs.find(c => c.id === prev.id);
          return fresh ? { ...prev, status: fresh.status, assigned_agent_id: fresh.assigned_agent_id } : prev;
        });
      }
      convs.forEach(c => fetchCustomer(c.customer_id));
      // Restore selected conversation from URL hash on initial load
      if (!silent && pendingHashId.current) {
        const restored = convs.find(c => c.id === pendingHashId.current);
        if (restored) setSelected(restored);
        pendingHashId.current = null;
      }
    } catch (err: any) {
      if (!silent) setError(err.response?.data?.detail || 'Erreur chargement');
    } finally { if (!silent) setLoading(false); }
  }, [statusFilter, fetchCustomer]);

  const fetchMessages = useCallback(async (id: string) => {
    try {
      const r = await api.get(`/conversations/conversations/${id}/messages`, { params: { limit: 500 } });
      setMessages(r.data);
    } catch {}
  }, []);

  useEffect(() => {
    if (!user) return;
    fetchConversations();
    fetchAgents();
    // Silent polling every 8s
    pollConvRef.current = setInterval(() => fetchConversations(true), 8000);
    return () => { if (pollConvRef.current) clearInterval(pollConvRef.current); };
  }, [user, statusFilter]);

  useEffect(() => {
    if (!selected) return;
    fetchMessages(selected.id);
    inputRef.current?.focus();
    const iv = setInterval(() => fetchMessages(selected.id), 4000);
    return () => clearInterval(iv);
  }, [selected]);

  useEffect(() => {
    if (!messagesEndRef.current) return;
    const isNewConv = prevSelectedId.current !== selected?.id;
    prevSelectedId.current = selected?.id ?? null;
    messagesEndRef.current.scrollIntoView({ behavior: isNewConv ? 'instant' : 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !newMessage.trim()) return;
    setSending(true);
    try {
      await api.post(`/conversations/conversations/${selected.id}/messages`, { content: newMessage.trim(), message_type: 'TEXT' });
      setNewMessage('');
      fetchMessages(selected.id);
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur envoi'); }
    finally { setSending(false); }
  };

  const handleAutoAssign = async () => {
    setAutoAssigning(true); setAutoAssignMsg('');
    try {
      const r = await api.post('/conversations/auto-assign');
      const { assigned, skipped } = r.data;
      setAutoAssignMsg(
        assigned === 0
          ? 'Aucune conversation non assignée à distribuer.'
          : `✅ ${assigned} conversation${assigned > 1 ? 's' : ''} assignée${assigned > 1 ? 's' : ''} automatiquement${skipped > 0 ? ` (${skipped} ignorée${skipped > 1 ? 's' : ''})` : ''}.`
      );
      fetchConversations();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur auto-assign'); }
    finally { setAutoAssigning(false); }
  };

  const handleTake = async () => {
    if (!selected) return;
    try {
      await api.post(`/conversations/conversations/${selected.id}/take`);
      fetchConversations();
      setSelected(prev => prev ? { ...prev, assigned_agent_id: user?.id || null, status: 'AGENT' } : prev);
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
  };

  const handleChangeStatus = async () => {
    if (!selected || !modalStatus) return;
    try {
      await api.post(`/conversations/conversations/${selected.id}/status`, { status: modalStatus });
      setShowStatusModal(false);
      setSelected(prev => prev ? { ...prev, status: modalStatus } : prev);
      fetchConversations();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
  };

  const handleAssign = async () => {
    if (!selected || !modalAgentId) return;
    try {
      await api.post(`/conversations/conversations/${selected.id}/assign`, { agent_id: modalAgentId });
      setShowAssignModal(false); setModalAgentId('');
      fetchConversations();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
  };

  const handleAddTag = async () => {
    if (!selected || !modalTag.trim()) return;
    try {
      await api.post(`/conversations/conversations/${selected.id}/tags`, { tag: modalTag.trim() });
      setShowTagModal(false); setModalTag('');
      fetchConversations();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur'); }
  };

  const handleDeleteConversation = async () => {
    if (!selected) return;
    if (!confirm('Supprimer cette conversation et tous ses messages ? Cette action est irréversible.')) return;
    try {
      await api.delete(`/conversations/conversations/${selected.id}`);
      setSelected(null);
      setMessages([]);
      fetchConversations();
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur suppression'); }
  };

  const handleDeleteMessage = async (msgId: string) => {
    if (!selected) return;
    if (!confirm('Supprimer ce message ?')) return;
    try {
      await api.delete(`/conversations/conversations/${selected.id}/messages/${msgId}`);
      setMessages(prev => prev.filter(m => m.id !== msgId));
    } catch (err: any) { setError(err.response?.data?.detail || 'Erreur suppression message'); }
  };

  const assignedAgent = selected?.assigned_agent_id
    ? agents.find(a => a.id === selected.assigned_agent_id) : null;

  const filtered = conversations.filter(c => {
    if (!searchQ) return true;
    const q = searchQ.toLowerCase();
    const cust = customers[c.customer_id];
    return (
      (cust?.name?.toLowerCase().includes(q)) ||
      (cust?.phone_number?.includes(q)) ||
      c.id.includes(q)
    );
  });

  const waitingCount = conversations.filter(c => c.status === 'WAITING').length;

  const isMine = selected ? selected.assigned_agent_id === user?.id : false;
  const isLocked = selected
    ? (selected.status === 'AI') ||
      (selected.status === 'WAITING' && !isMine && user?.role !== 'COMPANY_ADMIN' && user?.role !== 'SUPER_ADMIN') ||
      (!selected.assigned_agent_id && selected.status !== 'AGENT' && selected.status !== 'WAITING')
    : false;
  const canWrite = isMine || user?.role === 'COMPANY_ADMIN' || user?.role === 'SUPER_ADMIN';

  return (
    <AppLayout>
      <div className="h-full flex flex-col" style={{ height: 'calc(100vh - 112px)' }}>

        {/* ── Header ── */}
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <h1 className="text-xl font-bold text-gray-900 mr-auto">💬 Conversations</h1>
          <input value={searchQ} onChange={e => setSearchQ(e.target.value)}
            placeholder="🔍 Rechercher client, téléphone..."
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-56 focus:ring-2 focus:ring-green-500" />
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-green-500">
            <option value="">Tous les statuts</option>
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          {(user?.role === 'COMPANY_ADMIN' || user?.role === 'SUPER_ADMIN') && (
            <button onClick={handleAutoAssign} disabled={autoAssigning}
              className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5">
              {autoAssigning ? '⏳ Attribution…' : '⚡ Auto-assign'}
            </button>
          )}
        </div>
        {autoAssignMsg && (
          <div className={`text-sm px-4 py-2 rounded-lg mb-3 flex justify-between items-center ${
            autoAssignMsg.startsWith('✅') ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-gray-50 text-gray-600 border border-gray-200'
          }`}>
            <span>{autoAssignMsg}</span>
            <button onClick={() => setAutoAssignMsg('')} className="ml-2 opacity-60 hover:opacity-100">✕</button>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-3 flex justify-between text-sm">
            <span>{error}</span><button onClick={() => setError('')}>✕</button>
          </div>
        )}

        {waitingCount > 0 && (
          <div className="animate-pulse bg-amber-50 border border-amber-400 text-amber-800 px-4 py-2.5 rounded-lg mb-3 flex items-center justify-between text-sm font-medium">
            <span>🔔 <strong>{waitingCount} conversation{waitingCount > 1 ? 's' : ''}</strong> en attente d’intervention humaine (transfert bot)</span>
            <button onClick={() => setStatusFilter('WAITING')} className="text-xs bg-amber-400 text-white px-2.5 py-1 rounded-lg hover:bg-amber-500 ml-3 whitespace-nowrap">Voir</button>
          </div>
        )}

        <div className="flex gap-3 flex-1 min-h-0">

          {/* ── Liste ── */}
          <div className="w-72 flex-shrink-0 bg-white rounded-xl shadow flex flex-col overflow-hidden">
            <div className="px-4 py-2.5 bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {filtered.length} conversation{filtered.length !== 1 ? 's' : ''}
            </div>
            <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
              {loading ? (
                <div className="p-8 text-center text-gray-400 text-sm">Chargement…</div>
              ) : filtered.length === 0 ? (
                <div className="p-8 text-center text-gray-400 text-sm">Aucune conversation</div>
              ) : filtered.map(c => {
                const cust = customers[c.customer_id];
                const isSelected = selected?.id === c.id;
                const isUnassigned = !c.assigned_agent_id;
                return (
                  <div key={c.id} onClick={() => setSelected(c)}
                    className={`px-3 py-3 cursor-pointer hover:bg-gray-50 transition-colors relative ${
                      isSelected ? 'bg-green-50 border-l-4 border-green-500' :
                      c.status === 'WAITING' ? 'border-l-4 border-amber-400 bg-amber-50/40' :
                      'border-l-4 border-transparent'
                    }`}>
                    <div className="flex items-start justify-between gap-1 mb-0.5">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${PRIORITY_DOT[c.priority] || 'bg-gray-400'}`} title={c.priority} />
                        <span className="text-sm font-semibold text-gray-900 truncate">
                          {clientLabel(cust)}
                        </span>
                      </div>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full flex-shrink-0 ${STATUS_COLORS[c.status] || 'bg-gray-100 text-gray-600'}`}>
                        {c.status === 'WAITING' ? '🔔 WAITING' : c.status}
                      </span>
                    </div>
                    {cust?.phone_number && cust?.name && (
                      <p className="text-xs text-gray-400 ml-3.5 mb-0.5">{cust.phone_number}</p>
                    )}
                    <div className="flex items-center justify-between ml-3.5">
                      <span className="text-xs text-gray-400">
                        {new Date(c.last_activity_at).toLocaleString('fr-FR', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}
                      </span>
                      {isUnassigned && (
                        <span className="text-xs text-amber-600 font-medium">Non assigné</span>
                      )}
                    </div>
                    {c.tags && c.tags.length > 0 && (
                      <div className="flex gap-1 mt-1 ml-3.5 flex-wrap">
                        {c.tags.map((t, i) => (
                          <span key={i} className="text-xs bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Zone centrale + panneau client ── */}
          <div className="flex-1 flex gap-3 min-w-0 min-h-0">

            {/* Chat */}
            <div className="flex-1 bg-white rounded-xl shadow flex flex-col overflow-hidden min-w-0 min-h-0">
              {selected ? (
                <>
                  {/* Header chat */}
                  <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-8 h-8 rounded-full bg-green-100 text-green-700 flex items-center justify-center font-bold text-sm flex-shrink-0">
                        {clientLabel(customers[selected.customer_id]).charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-gray-900 text-sm truncate">{clientLabel(customers[selected.customer_id])}</p>
                        <div className="flex items-center gap-1.5">
                          <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full ${STATUS_COLORS[selected.status]}`}>{selected.status}</span>
                          <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full ${PRIORITY_DOT[selected.priority].replace('bg-', 'bg-').replace('-400','-100').replace('-500','-100')} text-gray-600`}>{selected.priority}</span>
                          {assignedAgent && <span className="text-xs text-gray-400">→ {assignedAgent.first_name} {assignedAgent.last_name}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1.5 flex-shrink-0 flex-wrap justify-end">
                      {!isMine && (
                        <button onClick={handleTake}
                          className="text-xs bg-green-100 text-green-700 px-2.5 py-1.5 rounded-lg hover:bg-green-200 font-semibold">
                          ✋ Prendre
                        </button>
                      )}
                      <button onClick={() => { setModalStatus(selected.status); setShowStatusModal(true); }}
                        className="text-xs bg-amber-100 text-amber-700 px-2.5 py-1.5 rounded-lg hover:bg-amber-200 font-medium">Statut</button>
                      <button onClick={() => setShowAssignModal(true)}
                        className="text-xs bg-blue-100 text-blue-700 px-2.5 py-1.5 rounded-lg hover:bg-blue-200 font-medium">Assigner</button>
                      <button onClick={() => setShowTagModal(true)}
                        className="text-xs bg-purple-100 text-purple-700 px-2.5 py-1.5 rounded-lg hover:bg-purple-200 font-medium">+ Tag</button>
                      <button onClick={handleDeleteConversation}
                        className="text-xs bg-red-100 text-red-700 px-2.5 py-1.5 rounded-lg hover:bg-red-200 font-medium" title="Supprimer la conversation">🗑️</button>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 bg-[#efeae2]" style={{backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23d4cfc8\' fill-opacity=\'0.3\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")'}}>
                    {messages.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-500 text-sm">Aucun message</div>
                    ) : (() => {
                      const sorted = [...messages].sort((a, b) => new Date(a.sent_at).getTime() - new Date(b.sent_at).getTime());
                      const items: React.ReactNode[] = [];
                      let lastDay = '';
                      let lastSender = '';
                      sorted.forEach((m, idx) => {
                        const d = new Date(m.sent_at);
                        const dayKey = d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
                        const today = new Date();
                        const yesterday = new Date(); yesterday.setDate(today.getDate() - 1);
                        const dayLabel =
                          dayKey === today.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }) ? "Aujourd'hui" :
                          dayKey === yesterday.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }) ? 'Hier' :
                          dayKey;
                        if (dayKey !== lastDay) {
                          lastDay = dayKey;
                          lastSender = '';
                          items.push(
                            <div key={`day-${dayKey}`} className="flex items-center gap-3 my-4">
                              <div className="flex-1 h-px bg-gray-300/60" />
                              <span className="text-xs text-gray-500 font-medium px-3 py-1 bg-white/80 rounded-full shadow-sm">{dayLabel}</span>
                              <div className="flex-1 h-px bg-gray-300/60" />
                            </div>
                          );
                        }
                        const isOutgoing = m.sender_type === 'AGENT' || m.sender_type === 'BOT';
                        const isCustomer = m.sender_type === 'CUSTOMER';
                        const senderKey = m.sender_type + (m.sender_id || '');
                        const showAvatar = isCustomer && senderKey !== lastSender;
                        lastSender = senderKey;
                        const cust = customers[selected!.customer_id];
                        const custInitial = clientLabel(cust).charAt(0).toUpperCase();

                        items.push(
                          <div key={m.id} className={`flex items-end gap-2 mb-1 ${isOutgoing ? 'justify-end' : 'justify-start'}`}>
                            {/* Avatar client */}
                            {isCustomer && (
                              showAvatar
                                ? <div className="w-7 h-7 rounded-full bg-gray-400 text-white flex items-center justify-center text-xs font-bold flex-shrink-0 mb-0.5">{custInitial}</div>
                                : <div className="w-7 flex-shrink-0" />
                            )}
                            <div className={`max-w-[65%] flex flex-col ${isOutgoing ? 'items-end' : 'items-start'}`}>
                              {/* Label expéditeur (1ère bulle du groupe) */}
                              {m.sender_type === 'BOT' && (
                                <span className="text-xs text-purple-600 font-medium mb-0.5 ml-1">🤖 Bot</span>
                              )}
                              {m.sender_type === 'AGENT' && showAvatar && (
                                <span className="text-xs text-green-700 font-medium mb-0.5 mr-1">Agent</span>
                              )}
                              <div className={`relative group px-3.5 py-2 shadow-sm text-sm whitespace-pre-wrap break-words ${
                                m.sender_type === 'AGENT'
                                  ? 'bg-[#dcf8c6] text-gray-900 rounded-2xl rounded-br-sm'
                                  : m.sender_type === 'BOT'
                                  ? 'bg-[#e9d5ff] text-gray-900 rounded-2xl rounded-br-sm'
                                  : 'bg-white text-gray-900 rounded-2xl rounded-bl-sm'
                              }`}>
                                <button onClick={() => handleDeleteMessage(m.id)}
                                  className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow" title="Supprimer">✕</button>
                                {m.content || <span className="italic text-gray-400">(média)</span>}
                                <span className={`text-[10px] ml-2 float-right mt-1 ${isOutgoing ? 'text-gray-500' : 'text-gray-400'} flex items-center gap-0.5 float-right`}>
                                  {d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                                  {isOutgoing && (() => {
                                    const s = m.status;
                                    if (s === 'FAILED') return <span className="text-red-500 ml-1">✕</span>;
                                    if (s === 'READ')      return <span className="text-blue-500 ml-1">✓✓</span>;
                                    if (s === 'DELIVERED') return <span className="text-gray-500 ml-1">✓✓</span>;
                                    if (s === 'SENT')      return <span className="text-gray-400 ml-1">✓</span>;
                                    return <span className="text-gray-300 ml-1">🕐</span>;
                                  })()}
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      });
                      return items;
                    })()}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  {isLocked && canWrite ? (
                    <div className="border-t p-3 bg-amber-50 flex items-center gap-3">
                      <span className="text-sm text-amber-700 flex-1">
                        {selected.status === 'AI'
                          ? '🤖 Bot actif — cliquez "Prendre" pour reprendre la main'
                          : selected.status === 'WAITING'
                          ? '⏳ En attente de votre première réponse — écrivez pour activer AGENT'
                          : '⏳ Non assigné — prenez la main ou assignez un agent'}
                      </span>
                      <button onClick={handleTake}
                        className="text-xs bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 font-semibold whitespace-nowrap">
                        ✋ Prendre la main
                      </button>
                    </div>
                  ) : isLocked ? (
                    <div className="border-t p-3 bg-gray-50 text-center text-sm text-gray-400">
                      🔒 Conversation gérée par le bot ou non assignée
                    </div>
                  ) : (
                    <form onSubmit={handleSend} className="border-t p-3 flex gap-2 bg-white">
                      <input ref={inputRef}
                        value={newMessage}
                        onChange={e => setNewMessage(e.target.value)}
                        placeholder="Écrire un message… (Entrée pour envoyer)"
                        className="flex-1 border border-gray-300 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-green-500"
                      />
                      <button type="submit" disabled={sending || !newMessage.trim()}
                        className="bg-green-600 text-white px-4 py-2 rounded-xl hover:bg-green-700 disabled:opacity-50 text-sm font-semibold">
                        {sending ? '…' : '➤'}
                      </button>
                    </form>
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <span className="text-5xl mb-3">💬</span>
                  <p className="text-sm">Sélectionner une conversation</p>
                </div>
              )}
            </div>

            {/* ── Panneau client ── */}
            {selected && (
              <div className="w-56 bg-white rounded-xl shadow p-4 flex-shrink-0 flex flex-col gap-4 overflow-y-auto">
                {(() => {
                  const cust = customers[selected.customer_id];
                  return (
                    <>
                      <div className="text-center">
                        <div className="w-14 h-14 rounded-full bg-green-100 text-green-700 flex items-center justify-center font-bold text-xl mx-auto mb-2">
                          {clientLabel(cust).charAt(0).toUpperCase()}
                        </div>
                        <p className="font-semibold text-gray-900 text-sm">{clientLabel(cust)}</p>
                        {cust?.name && <p className="text-xs text-gray-400 mt-0.5">{cust.phone_number}</p>}
                      </div>

                      <div className="space-y-2 text-xs">
                        <div className="bg-gray-50 rounded-lg p-2.5">
                          <p className="text-gray-400 font-medium mb-0.5">Statut conv.</p>
                          <span className={`font-semibold px-1.5 py-0.5 rounded-full ${STATUS_COLORS[selected.status]}`}>{selected.status}</span>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2.5">
                          <p className="text-gray-400 font-medium mb-0.5">Priorité</p>
                          <div className="flex items-center gap-1">
                            <span className={`w-2 h-2 rounded-full ${PRIORITY_DOT[selected.priority]}`} />
                            <span className="font-semibold text-gray-700">{selected.priority}</span>
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-2.5">
                          <p className="text-gray-400 font-medium mb-0.5">Agent assigné</p>
                          <p className="font-semibold text-gray-700">
                            {assignedAgent ? `${assignedAgent.first_name} ${assignedAgent.last_name}` : '—'}
                          </p>
                          {isMine && <p className="text-green-600 text-xs mt-0.5">C'est vous ✓</p>}
                        </div>
                        {cust?.last_seen_at && (
                          <div className="bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 font-medium mb-0.5">Dernière activité</p>
                            <p className="font-semibold text-gray-700">
                              {new Date(cust.last_seen_at).toLocaleDateString('fr-FR', { day:'2-digit', month:'short', year:'numeric' })}
                            </p>
                          </div>
                        )}
                        {selected.tags && selected.tags.length > 0 && (
                          <div className="bg-gray-50 rounded-lg p-2.5">
                            <p className="text-gray-400 font-medium mb-1">Tags</p>
                            <div className="flex flex-wrap gap-1">
                              {selected.tags.map((t, i) => (
                                <span key={i} className="bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded text-xs">{t}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Modal Statut ── */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-80 shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">Changer le statut</h3>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {STATUSES.map(s => (
                <button key={s} onClick={() => setModalStatus(s)}
                  className={`py-2 rounded-lg text-sm font-medium border-2 transition-colors ${modalStatus === s ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 text-gray-600 hover:border-gray-300'}`}>{s}</button>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowStatusModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
              <button onClick={handleChangeStatus} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700">Appliquer</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal Assigner ── */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-80 shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">Assigner un agent</h3>
            <select value={modalAgentId} onChange={e => setModalAgentId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:ring-2 focus:ring-green-500">
              <option value="">— Choisir un agent —</option>
              {agents.map(a => (
                <option key={a.id} value={a.id}>{a.first_name} {a.last_name} ({a.email})</option>
              ))}
            </select>
            <div className="flex gap-2">
              <button onClick={() => setShowAssignModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
              <button onClick={handleAssign} disabled={!modalAgentId} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">Assigner</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal Tag ── */}
      {showTagModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-80 shadow-xl">
            <h3 className="font-bold text-gray-900 mb-4">Ajouter un tag</h3>
            <input type="text" value={modalTag} onChange={e => setModalTag(e.target.value)}
              placeholder="Ex: urgent, support, vente…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:ring-2 focus:ring-green-500"
              onKeyDown={e => e.key === 'Enter' && handleAddTag()}
            />
            <div className="flex gap-2">
              <button onClick={() => setShowTagModal(false)} className="flex-1 border border-gray-300 py-2 rounded-lg text-sm hover:bg-gray-50">Annuler</button>
              <button onClick={handleAddTag} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700">Ajouter</button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
