import { useState, useEffect, useRef, useCallback } from 'react';
import { notificationsService, Notification, NotificationPreference } from '../services/notifications';

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  const fetchNotifications = useCallback(async (params?: { skip?: number; limit?: number; unread_only?: boolean }) => {
    try {
      setLoading(true);
      const data = await notificationsService.getNotifications(params);
      setNotifications(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const data = await notificationsService.getUnreadCount();
      setUnreadCount(data.unread_count);
    } catch (err: any) {
      console.error('Failed to fetch unread count:', err);
    }
  }, []);

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await notificationsService.markAsRead(notificationId);
      await fetchNotifications();
      await fetchUnreadCount();
      
      // Send WebSocket message to update unread count
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'mark_as_read',
          notification_id: notificationId
        }));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to mark notification as read');
    }
  }, [fetchNotifications, fetchUnreadCount]);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsService.markAllAsRead();
      await fetchNotifications();
      await fetchUnreadCount();
      
      // Send WebSocket message to update unread count
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'mark_all_as_read' }));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to mark all notifications as read');
    }
  }, [fetchNotifications, fetchUnreadCount]);

  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      await notificationsService.deleteNotification(notificationId);
      await fetchNotifications();
      await fetchUnreadCount();
    } catch (err: any) {
      setError(err.message || 'Failed to delete notification');
    }
  }, [fetchNotifications, fetchUnreadCount]);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = notificationsService.createWebSocketConnection();
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('WebSocket connected');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'unread_count') {
            setUnreadCount(data.count);
          } else if (data.id) {
            // New notification received
            setNotifications(prev => [data, ...prev]);
            setUnreadCount(prev => prev + 1);
            
            // Play notification sound
            playNotificationSound();
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          // Reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchNotifications({ limit: 20 });
    fetchUnreadCount();
  }, [fetchNotifications, fetchUnreadCount]);

  const playNotificationSound = () => {
    const audio = new Audio('/sounds/notification.mp3');
    audio.play().catch(err => console.error('Failed to play notification sound:', err));
  };

  return {
    notifications,
    unreadCount,
    loading,
    error,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  };
}

export function useNotificationPreferences() {
  const [preferences, setPreferences] = useState<NotificationPreference[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPreferences = async () => {
    try {
      setLoading(true);
      const data = await notificationsService.getPreferences();
      setPreferences(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch notification preferences');
    } finally {
      setLoading(false);
    }
  };

  const updatePreference = async (data: { notification_type: string; enabled: boolean; channel?: string }) => {
    try {
      const updated = await notificationsService.updatePreference(data);
      setPreferences(prev => prev.map(p => p.id === updated.id ? updated : p));
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to update notification preference');
    }
  };

  useEffect(() => {
    fetchPreferences();
  }, []);

  return {
    preferences,
    loading,
    error,
    fetchPreferences,
    updatePreference,
  };
}
