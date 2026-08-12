'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';
import AppLayout from '../../components/AppLayout';

interface BotConfiguration {
  id: string;
  company_id: string;
  bot_type: string;
  name: string;
  ml_enabled: boolean;
  ml_provider: string | null;
  ml_model: string | null;
  ml_temperature: string | null;
  ml_max_tokens: number | null;
  confidence_threshold: string | null;
}

export default function MLConfigPage() {
  const [config, setConfig] = useState<BotConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [mlProviders, setMlProviders] = useState<any[]>([]);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchConfig();
      fetchMlProviders();
    }
  }, [user]);

  const fetchConfig = async () => {
    try {
      const response = await api.get('/bot/config');
      setConfig(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch configuration');
    } finally {
      setLoading(false);
    }
  };

  const fetchMlProviders = async () => {
    try {
      const response = await api.get('/ml/provider-configs/public');
      setMlProviders(response.data);
    } catch (err: any) {
      console.error('Failed to fetch ML providers:', err);
    }
  };

  const handleSave = async () => {
    if (!config) return;

    setSaving(true);
    try {
      await api.put('/bot/config', config);
      alert('Configuration saved successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof BotConfiguration, value: any) => {
    if (config) {
      setConfig({ ...config, [field]: value });
    }
  };

  if (loading) {
    return <AppLayout><div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div></AppLayout>;
  }

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Configuration ML</h1>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm">
            <span>{error}</span>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}

        {config && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Paramètres du Bot</h2>
            
            {/* Bot Type */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bot Type
              </label>
              <select
                value={config.bot_type}
                onChange={(e) => handleChange('bot_type', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="NATIVE">Native (with ML fallback)</option>
                <option value="ML">ML Only</option>
              </select>
            </div>

            {/* ML Enabled */}
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.ml_enabled}
                  onChange={(e) => handleChange('ml_enabled', e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Enable ML</span>
              </label>
            </div>

            {config.ml_enabled && (
              <>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 mt-6">ML Settings</h3>
                
                {/* ML Provider */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ML Provider
                  </label>
                  <select
                    value={config.ml_provider || ''}
                    onChange={(e) => handleChange('ml_provider', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="">Select Provider</option>
                    {mlProviders.map((provider) => (
                      <option key={provider.id} value={provider.provider_type}>
                        {provider.provider_type}
                      </option>
                    ))}
                  </select>
                </div>

                {/* ML Model */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model Name
                  </label>
                  <input
                    type="text"
                    value={config.ml_model || ''}
                    onChange={(e) => handleChange('ml_model', e.target.value)}
                    placeholder="e.g., gpt-3.5-turbo, claude-3-sonnet"
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>

                {/* Temperature */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature (0.0 - 1.0)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={config.ml_temperature || '0.7'}
                    onChange={(e) => handleChange('ml_temperature', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>

                {/* Max Tokens */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={config.ml_max_tokens || 500}
                    onChange={(e) => handleChange('ml_max_tokens', parseInt(e.target.value))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>

                {/* Confidence Threshold */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Confidence Threshold (0.0 - 1.0)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={config.confidence_threshold || '0.5'}
                    onChange={(e) => handleChange('confidence_threshold', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  />
                </div>
              </>
            )}

            <div className="flex justify-end mt-6">
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
