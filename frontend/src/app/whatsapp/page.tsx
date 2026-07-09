'use client';

import { useState, useEffect } from 'react';
import { useHashTab } from '../../hooks/useHashTab';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

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
}
interface WebhookInfo {
  webhook_url: string;
  verify_token: string;
  verify_token_configured: boolean;
  events_to_subscribe: string[];
}

function SuperAdminWebhookPanel() {
  const [webhookInfo, setWebhookInfo] = useState<WebhookInfo | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/whatsapp/webhook/info').then(r => setWebhookInfo(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const copy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  if (loading) return <div className="text-gray-400 text-sm">Chargement…</div>;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">🔗 Webhook Meta — Configuration globale</h1>
        <p className="text-sm text-gray-500">
          À configurer <strong>une seule fois</strong> sur Meta for Developers. Toutes les entreprises partagent ce même endpoint — le routage se fait automatiquement par <code className="bg-gray-100 px-1 rounded">phone_number_id</code>.
        </p>
      </div>

      {/* Statut */}
      <div className={`rounded-xl border-2 p-4 flex items-start gap-3 ${webhookInfo?.verify_token_configured ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
        <span className="text-2xl">{webhookInfo?.verify_token_configured ? '✅' : '❌'}</span>
        <div>
          <p className={`font-semibold text-sm ${webhookInfo?.verify_token_configured ? 'text-green-800' : 'text-red-800'}`}>
            {webhookInfo?.verify_token_configured
              ? 'WHATSAPP_WEBHOOK_VERIFY_TOKEN configuré — le backend accepte les vérifications Meta'
              : 'WHATSAPP_WEBHOOK_VERIFY_TOKEN manquant dans backend/.env'}
          </p>
          {!webhookInfo?.verify_token_configured && (
            <p className="text-xs text-red-600 mt-1">
              Ajoute <code className="bg-red-100 px-1 rounded">WHATSAPP_WEBHOOK_VERIFY_TOKEN=mon_secret_unique</code> dans <code className="bg-red-100 px-1 rounded">backend/.env</code> et redémarre le serveur.
            </p>
          )}
        </div>
      </div>

      {/* Infos à copier */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
        <h2 className="font-semibold text-gray-900">📋 Valeurs à saisir sur Meta for Developers</h2>

        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">URL du Webhook</label>
          <div className="mt-1 flex items-center gap-2">
            <code className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono text-gray-800 break-all">
              {webhookInfo?.webhook_url || '—'}
            </code>
            <button onClick={() => webhookInfo && copy(webhookInfo.webhook_url, 'url')}
              className="flex-shrink-0 bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-2 rounded-lg text-xs font-medium">
              {copied === 'url' ? '✓ Copié' : 'Copier'}
            </button>
          </div>
          <p className="text-xs text-amber-600 mt-1">⚠️ Meta exige HTTPS. Utilise Cloudflare Tunnel ou ngrok pour exposer le backend.</p>
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Token de vérification (Verify Token)</label>
          <div className="mt-1 flex items-center gap-2">
            <code className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono text-gray-800">
              {webhookInfo?.verify_token || '—'}
            </code>
            <span className="text-xs text-gray-400 flex-shrink-0">(masqué)</span>
          </div>
          <p className="text-xs text-gray-400 mt-1">Défini dans <code className="bg-gray-100 px-1 rounded">backend/.env</code> → <code className="bg-gray-100 px-1 rounded">WHATSAPP_WEBHOOK_VERIFY_TOKEN</code></p>
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Événements à activer (Webhook Fields)</label>
          <div className="mt-1 flex gap-2">
            {(webhookInfo?.events_to_subscribe || ['messages', 'message_status']).map(e => (
              <span key={e} className="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-full text-xs font-mono">{e}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Guide */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-900 mb-4">🧭 Étapes sur Meta for Developers</h2>
        <ol className="space-y-4">
          {[
            { n:'1', title:'Créer l\'app Meta', body:<span>Sur <a href="https://developers.facebook.com/apps" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">developers.facebook.com/apps</a> → <strong>Créer une application</strong> → type <strong>Business</strong> → ajouter le produit <strong>WhatsApp</strong>.</span> },
            { n:'2', title:'Configurer le Webhook', body:<span><strong>WhatsApp → Configuration → Webhook → Modifier</strong><br/>Coller l'<strong>URL</strong> et le <strong>Token de vérification</strong> ci-dessus → <strong>"Vérifier et enregistrer"</strong>.</span> },
            { n:'3', title:'S\'abonner aux événements', body:<span>Dans la liste des champs Webhook → activer <code className="bg-gray-100 px-1 rounded text-xs">messages</code> et <code className="bg-gray-100 px-1 rounded text-xs">message_status</code> → <strong>"S'abonner"</strong>.</span> },
            { n:'4', title:'Chaque admin d\'entreprise', body:<span>Va dans <strong>WhatsApp → Connexion</strong> pour saisir son <strong>Phone Number ID</strong> et son <strong>Access Token</strong> permanent. Le système route automatiquement les messages vers la bonne entreprise.</span> },
          ].map(step => (
            <li key={step.n} className="flex gap-3">
              <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">{step.n}</span>
              <div>
                <p className="text-sm font-semibold text-gray-800">{step.title}</p>
                <p className="text-sm text-gray-600 mt-0.5">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      {/* HTTPS */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
        <p className="font-semibold text-indigo-900 text-sm mb-1">💡 Exposer le backend en HTTPS (requis par Meta)</p>
        <code className="block bg-indigo-100 rounded-lg px-3 py-2 mt-1 text-xs font-mono text-indigo-800">cloudflared tunnel --url http://localhost:8000</code>
        <p className="text-xs text-indigo-700 mt-1">L'URL générée (<code>https://xxx.trycloudflare.com</code>) remplace la base de l'URL webhook ci-dessus.</p>
      </div>
    </div>
  );
}

export default function WhatsAppPage() {
  const [messages, setMessages]   = useState<WhatsAppMessage[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [credentials, setCredentials] = useState<WACredentials | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [success, setSuccess]     = useState('');
  const [activeTab, setActiveTab] = useHashTab<'connexion' | 'messages' | 'templates'>('connexion');
  const [submitting, setSubmitting] = useState(false);
  const [credForm, setCredForm]   = useState({ phone_number_id: '', access_token: '', waba_id: '', display_phone_number: '' });
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchCredentials();
      fetchMessages();
      fetchTemplates();
    }
  }, [user]);

  const fetchCredentials = async () => {
    try {
      const r = await api.get('/channels/whatsapp/credentials');
      setCredentials(r.data);
      if (r.data.configured) {
        setCredForm(f => ({ ...f, phone_number_id: r.data.phone_number_id || '', waba_id: r.data.waba_id || '', display_phone_number: r.data.display_phone_number || '' }));
      }
    } catch {} finally { setLoading(false); }
  };

  const saveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const r = await api.post('/channels/whatsapp/credentials', credForm);
      setSuccess('Connexion WhatsApp enregistrée !');
      setCredentials({ configured: true, ...r.data });
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

  if (user?.role === 'SUPER_ADMIN') {
    return (
      <AppLayout>
        <SuperAdminWebhookPanel />
      </AppLayout>
    );
  }

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
          <div className="max-w-xl">
            {credentials?.configured && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6 flex items-start gap-3">
                <span className="text-2xl">✅</span>
                <div>
                  <p className="font-semibold text-green-800 text-sm">WhatsApp connecté</p>
                  <p className="text-xs text-green-700 mt-0.5">Numéro : <span className="font-mono">{credentials.display_phone_number || '—'}</span></p>
                  <p className="text-xs text-green-700">Phone Number ID : <span className="font-mono">{credentials.phone_number_id}</span></p>
                  <p className="text-xs text-green-700">Token : <span className="font-mono">{credentials.access_token_masked}</span></p>
                </div>
              </div>
            )}

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-1">{credentials?.configured ? '✏️ Modifier la connexion' : '🔌 Connecter votre WhatsApp Business'}</h2>
              <p className="text-xs text-gray-500 mb-5">
                Ces informations vous sont fournies par votre administrateur de plateforme après création de votre compte WhatsApp Business sur <a href="https://business.facebook.com" target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">business.facebook.com</a>.
              </p>

              <form onSubmit={saveCredentials} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number ID <span className="text-red-500">*</span></label>
                  <input required value={credForm.phone_number_id}
                    onChange={e => setCredForm({...credForm, phone_number_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                    placeholder="123456789012345" />
                  <p className="text-xs text-gray-400 mt-1">Identifiant unique du numéro dans Meta.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Access Token (Permanent) <span className="text-red-500">*</span></label>
                  <input required type="password" value={credForm.access_token}
                    onChange={e => setCredForm({...credForm, access_token: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-green-500"
                    placeholder="EAAxxxxxxxxx..." />
                  <p className="text-xs text-gray-400 mt-1">Générez un token permanent depuis Meta Business Manager.</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">WABA ID <span className="text-gray-400 font-normal">(optionnel)</span></label>
                  <input value={credForm.waba_id}
                    onChange={e => setCredForm({...credForm, waba_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                    placeholder="WhatsApp Business Account ID" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Numéro affiché <span className="text-gray-400 font-normal">(optionnel)</span></label>
                  <input value={credForm.display_phone_number}
                    onChange={e => setCredForm({...credForm, display_phone_number: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    placeholder="+33 6 12 34 56 78" />
                </div>

                <button type="submit" disabled={submitting}
                  className="w-full bg-green-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50">
                  {submitting ? 'Enregistrement...' : credentials?.configured ? '💾 Mettre à jour' : '🔌 Connecter WhatsApp'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Messages Tab */}
        {activeTab === 'messages' && (
          <div className="bg-white shadow rounded-xl overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['Téléphone', 'Direction', 'Contenu', 'Statut', 'Date'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {messages.map(msg => (
                  <tr key={msg.id} className="hover:bg-gray-50">
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
    </AppLayout>
  );
}
