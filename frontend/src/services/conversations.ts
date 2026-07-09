// Conversations API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Conversation {
  id: string;
  company_id: string;
  customer_id: string;
  channel_id?: string;
  status: string;
  priority: string;
  assigned_agent_id?: string;
  tags?: string[];
  last_activity_at: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: string;
  sender_id?: string;
  content?: string;
  message_type: string;
  media_url?: string;
  external_message_id?: string;
  status: string;
  sent_at: string;
  delivered_at?: string;
  read_at?: string;
}

export interface Customer {
  id: string;
  company_id: string;
  phone_number: string;
  name?: string;
  profile_picture_url?: string;
  metadata?: Record<string, any>;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

class ConversationsService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getConversations(params?: { status?: string; skip?: number; limit?: number }): Promise<Conversation[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

    const response = await fetch(`${API_BASE}/conversations/?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch conversations');
    return response.json();
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch conversation');
    return response.json();
  }

  async assignAgent(conversationId: string, agentId: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/assign`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ agent_id: agentId }),
    });
    if (!response.ok) throw new Error('Failed to assign agent');
    return response.json();
  }

  async changeStatus(conversationId: string, status: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/status`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ status }),
    });
    if (!response.ok) throw new Error('Failed to change status');
    return response.json();
  }

  async addTag(conversationId: string, tag: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/tags`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ tag }),
    });
    if (!response.ok) throw new Error('Failed to add tag');
    return response.json();
  }

  async archiveConversation(conversationId: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/archive`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to archive conversation');
    return response.json();
  }

  async getMessages(conversationId: string, skip = 0, limit = 100): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages?skip=${skip}&limit=${limit}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch messages');
    return response.json();
  }

  async sendMessage(conversationId: string, content: string, messageType = 'TEXT', mediaUrl?: string): Promise<Message> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        content,
        message_type: messageType,
        media_url: mediaUrl,
      }),
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  }

  async addNote(conversationId: string, content: string): Promise<any> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/notes`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error('Failed to add note');
    return response.json();
  }
}

export const conversationsService = new ConversationsService();
