'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import api from '../../lib/api';

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
  fallback_strategy: string | null;
  confidence_threshold: string | null;
}

export default function MLConfigPage() {
  const [config, setConfig] = useState<BotConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchConfig();
    }
  }, [user]);

  const fetchConfig = async () => {
    try {
      const response = await api.get('/bot/configuration');
      setConfig(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;

    setSaving(true);
    try {
      await api.put(`/bot/configuration/${config.id}`, config);
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
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">ML Configuration</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {config && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Bot Settings</h2>
            
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
                <option value="NATIVE">Native</option>
                <option value="ML">ML Only</option>
                <option value="HYBRID">Hybrid</option>
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
                    <option value="OPENAI">OpenAI</option>
                    <option value="ANTHROPIC">Anthropic</option>
                    <option value="OLLAMA">Ollama</option>
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

                {/* Fallback Strategy */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fallback Strategy
                  </label>
                  <select
                    value={config.fallback_strategy || ''}
                    onChange={(e) => handleChange('fallback_strategy', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="">Select Strategy</option>
                    <option value="ML_TO_NATIVE">ML to Native</option>
                    <option value="NATIVE_TO_ML">Native to ML</option>
                    <option value="PARALLEL">Parallel</option>
                  </select>
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
    </div>
  );
}
