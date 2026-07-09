import { useState, useEffect } from 'react';
import { channelsService, Channel, ChannelCreateRequest, ChannelUpdateRequest } from '../services/channels';

export function useChannels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchChannels = async () => {
    try {
      setLoading(true);
      const data = await channelsService.getChannels();
      setChannels(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch channels');
    } finally {
      setLoading(false);
    }
  };

  const createChannel = async (data: ChannelCreateRequest) => {
    try {
      const newChannel = await channelsService.createChannel(data);
      setChannels([...channels, newChannel]);
      return newChannel;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to create channel');
    }
  };

  const updateChannel = async (channelId: string, data: ChannelUpdateRequest) => {
    try {
      const updatedChannel = await channelsService.updateChannel(channelId, data);
      setChannels(channels.map(ch => ch.id === channelId ? updatedChannel : ch));
      return updatedChannel;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update channel');
    }
  };

  const deleteChannel = async (channelId: string) => {
    try {
      await channelsService.deleteChannel(channelId);
      setChannels(channels.filter(ch => ch.id !== channelId));
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete channel');
    }
  };

  const verifyChannel = async (channelId: string) => {
    try {
      return await channelsService.verifyChannel(channelId);
    } catch (err: any) {
      throw new Error(err.message || 'Failed to verify channel');
    }
  };

  const testChannel = async (channelId: string) => {
    try {
      return await channelsService.testChannel(channelId);
    } catch (err: any) {
      throw new Error(err.message || 'Failed to test channel');
    }
  };

  useEffect(() => {
    fetchChannels();
  }, []);

  return {
    channels,
    loading,
    error,
    fetchChannels,
    createChannel,
    updateChannel,
    deleteChannel,
    verifyChannel,
    testChannel,
  };
}
