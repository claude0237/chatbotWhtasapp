// Notifications API Service
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Notification {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  message: string;
  data: Record<string, any> | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationPreference {
  id: string;
  user_id: string;
  notification_type: string;
  enabled: boolean;
  channel: string;
  created_at: string;
  updated_at: string;
}

class NotificationsService {
  private getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async getNotifications(params?: { skip?: number; limit?: number; unread_only?: boolean }): Promise<Notification[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.unread_only !== undefined) queryParams.append('unread_only', params.unread_only.toString());

    const response = await fetch(`${API_BASE}/notifications?${queryParams}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch notifications');
    return response.json();
  }

  async getUnreadCount(): Promise<{ unread_count: number }> {
    const response = await fetch(`${API_BASE}/notifications/unread-count`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch unread count');
    return response.json();
  }

  async markAsRead(notificationId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/notifications/${notificationId}/read`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to mark notification as read');
    return response.json();
  }

  async markAllAsRead(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/notifications/read-all`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to mark all notifications as read');
    return response.json();
  }

  async deleteNotification(notificationId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to delete notification');
    return response.json();
  }

  async getPreferences(): Promise<NotificationPreference[]> {
    const response = await fetch(`${API_BASE}/notifications/preferences`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch notification preferences');
    return response.json();
  }

  async updatePreference(data: { notification_type: string; enabled: boolean; channel?: string }): Promise<NotificationPreference> {
    const response = await fetch(`${API_BASE}/notifications/preferences`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update notification preference');
    return response.json();
  }

  createWebSocketConnection(): WebSocket {
    const token = localStorage.getItem('access_token');
    const wsUrl = API_BASE.replace('http', 'ws') + '/notifications/ws?token=' + token;
    return new WebSocket(wsUrl);
  }
}

export const notificationsService = new NotificationsService();
