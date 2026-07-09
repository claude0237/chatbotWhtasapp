import { useState, useEffect } from 'react';
import { botService, BotConfiguration, BotScenario, BotKeyword } from '../services/bot';

export function useBotConfig() {
  const [config, setConfig] = useState<BotConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const data = await botService.getBotConfig();
      setConfig(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch bot configuration');
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = async (data: Partial<BotConfiguration>) => {
    try {
      const updated = await botService.updateBotConfig(data);
      setConfig(updated);
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update bot configuration');
    }
  };

  const createConfig = async (data: Partial<BotConfiguration>) => {
    try {
      const created = await botService.createBotConfig(data);
      setConfig(created);
      return created;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to create bot configuration');
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  return {
    config,
    loading,
    error,
    fetchConfig,
    updateConfig,
    createConfig,
  };
}

export function useScenarios() {
  const [scenarios, setScenarios] = useState<BotScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchScenarios = async () => {
    try {
      setLoading(true);
      const data = await botService.getScenarios();
      setScenarios(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch scenarios');
    } finally {
      setLoading(false);
    }
  };

  const createScenario = async (data: Partial<BotScenario>) => {
    try {
      const created = await botService.createScenario(data);
      setScenarios([...scenarios, created]);
      return created;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to create scenario');
    }
  };

  const updateScenario = async (scenarioId: string, data: Partial<BotScenario>) => {
    try {
      const updated = await botService.updateScenario(scenarioId, data);
      setScenarios(scenarios.map(s => s.id === scenarioId ? updated : s));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update scenario');
    }
  };

  const deleteScenario = async (scenarioId: string) => {
    try {
      await botService.deleteScenario(scenarioId);
      setScenarios(scenarios.filter(s => s.id !== scenarioId));
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete scenario');
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  return {
    scenarios,
    loading,
    error,
    fetchScenarios,
    createScenario,
    updateScenario,
    deleteScenario,
  };
}

export function useKeywords() {
  const [keywords, setKeywords] = useState<BotKeyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchKeywords = async () => {
    try {
      setLoading(true);
      const data = await botService.getKeywords();
      setKeywords(data);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch keywords');
    } finally {
      setLoading(false);
    }
  };

  const createKeyword = async (data: Partial<BotKeyword>) => {
    try {
      const created = await botService.createKeyword(data);
      setKeywords([...keywords, created]);
      return created;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to create keyword');
    }
  };

  const updateKeyword = async (keywordId: string, data: Partial<BotKeyword>) => {
    try {
      const updated = await botService.updateKeyword(keywordId, data);
      setKeywords(keywords.map(k => k.id === keywordId ? updated : k));
      return updated;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to update keyword');
    }
  };

  const deleteKeyword = async (keywordId: string) => {
    try {
      await botService.deleteKeyword(keywordId);
      setKeywords(keywords.filter(k => k.id !== keywordId));
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete keyword');
    }
  };

  useEffect(() => {
    fetchKeywords();
  }, []);

  return {
    keywords,
    loading,
    error,
    fetchKeywords,
    createKeyword,
    updateKeyword,
    deleteKeyword,
  };
}
