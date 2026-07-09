// Channels API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Channel {
  id: string;
  company_id: string;
  channel_type: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ChannelCreateRequest {
  channel_type: string;
  name: string;
  configuration?: Record<string, any>;
}

export interface ChannelUpdateRequest {
  name?: string;
  status?: string;
  configuration?: Record<string, any>;
}

class ChannelsService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getChannels(): Promise<Channel[]> {
    const response = await fetch(`${API_BASE}/channels/`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch channels');
    return response.json();
  }

  async getChannel(channelId: string): Promise<Channel> {
    const response = await fetch(`${API_BASE}/channels/${channelId}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch channel');
    return response.json();
  }

  async createChannel(data: ChannelCreateRequest): Promise<Channel> {
    const response = await fetch(`${API_BASE}/channels/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create channel');
    return response.json();
  }

  async updateChannel(channelId: string, data: ChannelUpdateRequest): Promise<Channel> {
    const response = await fetch(`${API_BASE}/channels/${channelId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update channel');
    return response.json();
  }

  async deleteChannel(channelId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/channels/${channelId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete channel');
  }

  async verifyChannel(channelId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/channels/${channelId}/verify`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to verify channel');
    return response.json();
  }

  async testChannel(channelId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/channels/${channelId}/test`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to test channel');
    return response.json();
  }
}

export const channelsService = new ChannelsService();
