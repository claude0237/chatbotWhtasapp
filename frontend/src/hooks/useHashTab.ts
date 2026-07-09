'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * Persist the active tab in the URL hash so it survives page refresh.
 * Usage: const [activeTab, setActiveTab] = useHashTab<'a'|'b'>('a');
 */
export function useHashTab<T extends string>(defaultTab: T): [T, (tab: T) => void] {
  const readHash = (): T => {
    if (typeof window === 'undefined') return defaultTab;
    const hash = window.location.hash.replace('#', '');
    return (hash || defaultTab) as T;
  };

  const [tab, setTabState] = useState<T>(readHash);

  useEffect(() => {
    // On mount, read from hash (handles SSR hydration mismatch)
    const h = readHash();
    if (h !== tab) setTabState(h);
  }, []);

  const setTab = useCallback((newTab: T) => {
    setTabState(newTab);
    window.history.replaceState(null, '', `#${newTab}`);
  }, []);

  return [tab, setTab];
}
