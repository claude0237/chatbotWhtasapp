import { useState, useEffect } from 'react';
import { conversationsService, Conversation, Message } from '../services/conversations';

export function useConversations(params?: { status?: string; skip?: number; limit?: number }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const data = await conversationsService.getConversations(params);
      setConversations(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch conversations');
    } finally {
      setLoading(false);
    }
  };

  const assignAgent = async (conversationId: string, agentId: string) => {
    try {
      const updated = await conversationsService.assignAgent(conversationId, agentId);
      setConversations(conversations.map(c => c.id === conversationId ? updated : c));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to assign agent');
    }
  };

  const changeStatus = async (conversationId: string, status: string) => {
    try {
      const updated = await conversationsService.changeStatus(conversationId, status);
      setConversations(conversations.map(c => c.id === conversationId ? updated : c));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to change status');
    }
  };

  const addTag = async (conversationId: string, tag: string) => {
    try {
      const updated = await conversationsService.addTag(conversationId, tag);
      setConversations(conversations.map(c => c.id === conversationId ? updated : c));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to add tag');
    }
  };

  const archiveConversation = async (conversationId: string) => {
    try {
      const updated = await conversationsService.archiveConversation(conversationId);
      setConversations(conversations.filter(c => c.id !== conversationId));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to archive conversation');
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [params?.status, params?.skip, params?.limit]);

  return {
    conversations,
    loading,
    error,
    fetchConversations,
    assignAgent,
    changeStatus,
    addTag,
    archiveConversation,
  };
}

export function useMessages(conversationId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchMessages = async () => {
    try {
      setLoading(true);
      const data = await conversationsService.getMessages(conversationId);
      setMessages(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch messages');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (content: string, messageType = 'TEXT', mediaUrl?: string) => {
    try {
      const newMessage = await conversationsService.sendMessage(conversationId, content, messageType, mediaUrl);
      setMessages([...messages, newMessage]);
      return newMessage;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to send message');
    }
  };

  const addNote = async (content: string) => {
    try {
      return await conversationsService.addNote(conversationId, content);
    } catch (err: any) {
      throw new Error(err.message || 'Failed to add note');
    }
  };

  useEffect(() => {
    if (conversationId) {
      fetchMessages();
    }
  }, [conversationId]);

  return {
    messages,
    loading,
    error,
    fetchMessages,
    sendMessage,
    addNote,
  };
}
