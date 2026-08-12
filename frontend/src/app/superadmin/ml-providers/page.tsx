'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import api from '../../../lib/api';
import AppLayout from '../../../components/AppLayout';

interface MLProviderConfig {
  id: string;
  provider_type: string;
  is_active: boolean;
  api_key: string | null;
  api_endpoint: string | null;
  default_model: string | null;
  default_temperature: number | null;
  default_max_tokens: number | null;
  requests_per_minute: number | null;
  requests_per_day: number | null;
  extra_config: any;
  created_at: string;
  updated_at: string;
}

export default function SuperadminMLProvidersPage() {
  const [configs, setConfigs] = useState<MLProviderConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingConfig, setEditingConfig] = useState<MLProviderConfig | null>(null);
  const [showModal, setShowModal] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchConfigs();
    }
  }, [user]);

  const fetchConfigs = async () => {
    try {
      const response = await api.get('/ml/provider-configs');
      setConfigs(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch provider configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (providerType: string) => {
    try {
      await api.post(`/ml/provider-config/${providerType}/activate`);
      await fetchConfigs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to activate provider');
    }
  };

  const handleEdit = (config: MLProviderConfig) => {
    setEditingConfig(config);
    setShowModal(true);
  };

  const handleSave = async (formData: Partial<MLProviderConfig>) => {
    try {
      if (editingConfig) {
        await api.put(`/ml/provider-config/${editingConfig.provider_type}`, formData);
      } else {
        await api.post('/ml/provider-config', formData);
      }
      setShowModal(false);
      setEditingConfig(null);
      await fetchConfigs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    }
  };

  const handleDelete = async (providerType: string) => {
    if (!confirm('Are you sure you want to delete this provider configuration?')) {
      return;
    }
    try {
      await api.delete(`/ml/provider-config/${providerType}`);
      await fetchConfigs();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete configuration');
    }
  };

  if (loading) {
    return <AppLayout><div className="flex items-center justify-center h-64 text-gray-400">Chargement...</div></AppLayout>;
  }

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Configuration des Providers ML</h1>
          <button
            onClick={() => {
              setEditingConfig(null);
              setShowModal(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + Provider
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-2 rounded-lg mb-4 flex justify-between text-sm">
            <span>{error}</span>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {configs.map((config) => (
            <div
              key={config.id}
              className={`bg-white shadow rounded-lg p-6 border-2 ${
                config.is_active ? 'border-green-500' : 'border-gray-200'
              }`}
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{config.provider_type}</h3>
                {config.is_active && (
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                    Active
                  </span>
                )}
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <p><strong>Model:</strong> {config.default_model || 'Not configured'}</p>
                <p><strong>Temperature:</strong> {config.default_temperature || 'N/A'}</p>
                <p><strong>Max Tokens:</strong> {config.default_max_tokens || 'N/A'}</p>
                <p><strong>API Key:</strong> {config.api_key ? '••••••••' : 'Not set'}</p>
                <p><strong>Rate Limit:</strong> {config.requests_per_minute || 'N/A'} req/min</p>
              </div>

              <div className="flex justify-between items-center mt-4 pt-4 border-t">
                <div className="space-x-2">
                  <button
                    onClick={() => handleEdit(config)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(config.provider_type)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
                {!config.is_active && (
                  <button
                    onClick={() => handleActivate(config.provider_type)}
                    className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                  >
                    Activate
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {configs.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
            Aucun provider ML configuré. Cliquez sur "+ Provider" pour commencer.
          </div>
        )}

        {showModal && (
          <ProviderConfigModal
            config={editingConfig}
            onSave={handleSave}
            onCancel={() => {
              setShowModal(false);
              setEditingConfig(null);
            }}
          />
        )}
      </div>
    </AppLayout>
  );
}

function ProviderConfigModal({
  config,
  onSave,
  onCancel
}: {
  config: MLProviderConfig | null;
  onSave: (data: Partial<MLProviderConfig>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Partial<MLProviderConfig>>(
    config || {
      provider_type: 'MISTRAL',
      is_active: false,
      api_key: '',
      api_endpoint: '',
      default_model: '',
      default_temperature: 70,
      default_max_tokens: 500,
      requests_per_minute: null,
      requests_per_day: null
    }
  );

  const handleChange = (field: keyof MLProviderConfig, value: any) => {
    setFormData({ ...formData, [field]: value });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {config ? 'Edit Provider' : 'Add Provider'}
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider Type
            </label>
            <select
              value={formData.provider_type}
              onChange={(e) => handleChange('provider_type', e.target.value)}
              disabled={!!config}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="OPENAI">OpenAI</option>
              <option value="MISTRAL">Mistral</option>
              <option value="ANTHROPIC">Anthropic</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key
            </label>
            <input
              type="password"
              value={formData.api_key || ''}
              onChange={(e) => handleChange('api_key', e.target.value)}
              placeholder="Enter API key"
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Endpoint (optional)
            </label>
            <input
              type="text"
              value={formData.api_endpoint || ''}
              onChange={(e) => handleChange('api_endpoint', e.target.value)}
              placeholder="https://api.example.com"
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Model
            </label>
            <input
              type="text"
              value={formData.default_model || ''}
              onChange={(e) => handleChange('default_model', e.target.value)}
              placeholder="e.g., gpt-3.5-turbo, mistral-small-latest"
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature (0-200)
              </label>
              <input
                type="number"
                value={formData.default_temperature || 70}
                onChange={(e) => handleChange('default_temperature', parseInt(e.target.value))}
                min="0"
                max="200"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                value={formData.default_max_tokens || 500}
                onChange={(e) => handleChange('default_max_tokens', parseInt(e.target.value))}
                min="1"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Requests/Minute
              </label>
              <input
                type="number"
                value={formData.requests_per_minute || ''}
                onChange={(e) => handleChange('requests_per_minute', parseInt(e.target.value) || null)}
                min="1"
                placeholder="Optional"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Requests/Day
              </label>
              <input
                type="number"
                value={formData.requests_per_day || ''}
                onChange={(e) => handleChange('requests_per_day', parseInt(e.target.value) || null)}
                min="1"
                placeholder="Optional"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => handleChange('is_active', e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
              Set as active (will deactivate all other providers)
            </label>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(formData)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
