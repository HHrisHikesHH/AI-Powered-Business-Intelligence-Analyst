import { useState, useEffect } from 'react';
import type { QueryHistoryItem } from '@/types/api';

const STORAGE_KEY = 'ai-bi-query-history';
const MAX_HISTORY = 50;

export const useQueryHistory = () => {
  const [history, setHistory] = useState<QueryHistoryItem[]>(() => {
    // Load from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          return parsed.map((item: any) => ({
            ...item,
            timestamp: new Date(item.timestamp),
          }));
        } catch {
          return [];
        }
      }
    }
    return [];
  });

  useEffect(() => {
    // Save to localStorage whenever history changes
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  }, [history]);

  const addToHistory = (item: QueryHistoryItem) => {
    setHistory((prev) => {
      // Remove duplicates and keep only latest MAX_HISTORY items
      const filtered = prev.filter((h) => h.id !== item.id);
      return [item, ...filtered].slice(0, MAX_HISTORY);
    });
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const removeFromHistory = (id: string) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
  };

  return {
    history,
    addToHistory,
    clearHistory,
    removeFromHistory,
  };
};

