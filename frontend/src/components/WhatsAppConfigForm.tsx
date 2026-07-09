'use client';

import { useState } from 'react';
import { channelsService, ChannelCreateRequest } from '../services/channels';

interface WhatsAppConfigFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function WhatsAppConfigForm({ onSuccess, onCancel }: WhatsAppConfigFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    phone_number_id: '',
    access_token: '',
    webhook_verify_token: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const channelData: ChannelCreateRequest = {
        channel_type: 'WHATSAPP',
        name: formData.name,
        configuration: {
          phone_number_id: formData.phone_number_id,
          access_token: formData.access_token,
          webhook_verify_token: formData.webhook_verify_token,
        },
      };

      await channelsService.createChannel(channelData);
      
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to create WhatsApp channel');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Configure WhatsApp Channel</h2>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Channel Name
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="My WhatsApp Channel"
          />
        </div>

        <div>
          <label htmlFor="phone_number_id" className="block text-sm font-medium text-gray-700 mb-1">
            Phone Number ID
          </label>
          <input
            type="text"
            id="phone_number_id"
            value={formData.phone_number_id}
            onChange={(e) => setFormData({ ...formData, phone_number_id: e.target.value })}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="123456789012345"
          />
          <p className="text-xs text-gray-500 mt-1">From Meta Business Suite</p>
        </div>

        <div>
          <label htmlFor="access_token" className="block text-sm font-medium text-gray-700 mb-1">
            Access Token
          </label>
          <input
            type="password"
            id="access_token"
            value={formData.access_token}
            onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="EAAxxxxxxxxxxxxxxxxxxxxxxxx"
          />
          <p className="text-xs text-gray-500 mt-1">Permanent access token from Meta</p>
        </div>

        <div>
          <label htmlFor="webhook_verify_token" className="block text-sm font-medium text-gray-700 mb-1">
            Webhook Verify Token
          </label>
          <input
            type="text"
            id="webhook_verify_token"
            value={formData.webhook_verify_token}
            onChange={(e) => setFormData({ ...formData, webhook_verify_token: e.target.value })}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="my_verify_token_123"
          />
          <p className="text-xs text-gray-500 mt-1">Custom token for webhook verification</p>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Channel'}
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
