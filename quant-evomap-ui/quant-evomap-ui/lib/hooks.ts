'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

// Generic API query hook with loading/error/refetch
export function useApiQuery<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (mountedRef.current) {
        setData(result);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mountedRef.current = true;
    fetch();
    return () => {
      mountedRef.current = false;
    };
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

// Debounce hook
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

// Pagination state hook
export function usePagination(pageSize = 50) {
  const [offset, setOffset] = useState(0);
  const limit = pageSize;

  const nextPage = () => setOffset((o) => o + limit);
  const prevPage = () => setOffset((o) => Math.max(0, o - limit));
  const reset = () => setOffset(0);
  const currentPage = Math.floor(offset / limit) + 1;

  return { offset, limit, currentPage, nextPage, prevPage, reset };
}

// Auto-polling hook
export function usePolling(callback: () => void, interval = 30000, enabled = true) {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    if (!enabled) return;
    const timer = setInterval(() => callbackRef.current(), interval);
    return () => clearInterval(timer);
  }, [interval, enabled]);
}
