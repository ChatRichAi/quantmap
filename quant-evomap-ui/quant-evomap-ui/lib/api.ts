import type {
  Gene,
  GenesResponse,
  CapsulesResponse,
  EventsResponse,
  BountyTask,
  BountiesResponse,
  BountyStatus,
  CreateBountyPayload,
  MetricsResponse,
  EvolverStatus,
  StrategyListing,
  ListingsResponse,
  CreateListingPayload,
} from './types';

// ============================================================
// Core fetch utility
// ============================================================

const API_BASE_CLIENT = '/api/v1';
const API_BASE_SERVER = 'http://localhost:8889/api/v1';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const isBrowser = typeof window !== 'undefined';
  const base = isBrowser ? API_BASE_CLIENT : API_BASE_SERVER;
  const url = `${base}${path}`;

  const res = await fetch(url, {
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }

  const text = await res.text();
  return text ? JSON.parse(text) : ({} as T);
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ============================================================
// Genes
// ============================================================

export async function fetchGenes(limit = 50, offset = 0): Promise<GenesResponse> {
  return apiFetch<GenesResponse>(`/genes?limit=${limit}&offset=${offset}`);
}

export async function fetchGene(geneId: string): Promise<Gene> {
  return apiFetch<Gene>(`/genes/${geneId}`);
}

export async function submitGene(payload: { name: string; formula: string; [key: string]: unknown }): Promise<{ ok: boolean; gene_id: string }> {
  return apiPost('/genes', payload);
}

// ============================================================
// Capsules
// ============================================================

export async function fetchCapsules(limit = 50): Promise<CapsulesResponse> {
  return apiFetch<CapsulesResponse>(`/capsules?limit=${limit}`);
}

// ============================================================
// Events
// ============================================================

export async function fetchEvents(limit = 100): Promise<EventsResponse> {
  return apiFetch<EventsResponse>(`/events?limit=${limit}`);
}

// ============================================================
// Bounties
// ============================================================

export async function fetchBounties(status?: BountyStatus): Promise<BountiesResponse> {
  const query = status ? `?status=${status}` : '';
  return apiFetch<BountiesResponse>(`/bounties${query}`);
}

export async function createBounty(payload: CreateBountyPayload): Promise<{ ok: boolean; task_id: string }> {
  return apiPost('/bounties', payload);
}

export async function claimBounty(taskId: string, agentId: string): Promise<{ ok: boolean }> {
  return apiPost(`/bounties/${taskId}/claim`, { agent_id: agentId });
}

export async function submitBountyResult(
  taskId: string,
  agentId: string,
  bundleId: string
): Promise<{ ok: boolean }> {
  return apiPost(`/bounties/${taskId}/submit`, { agent_id: agentId, bundle_id: bundleId });
}

// ============================================================
// Metrics & Stats
// ============================================================

export async function fetchMetrics(): Promise<MetricsResponse> {
  return apiFetch<MetricsResponse>('/metrics');
}

export async function fetchEvolverStatus(): Promise<EvolverStatus> {
  return apiFetch<EvolverStatus>('/evolver/status');
}

// ============================================================
// Marketplace
// ============================================================

export async function fetchMarketListings(params?: {
  strategy_type?: string;
  min_sharpe?: number;
  max_price?: number;
  sort_by?: string;
}): Promise<ListingsResponse> {
  const q = new URLSearchParams();
  if (params?.strategy_type) q.set('strategy_type', params.strategy_type);
  if (params?.min_sharpe != null) q.set('min_sharpe', String(params.min_sharpe));
  if (params?.max_price != null) q.set('max_price', String(params.max_price));
  if (params?.sort_by) q.set('sort_by', params.sort_by);
  const qs = q.toString();
  return apiFetch<ListingsResponse>(`/market/listings${qs ? `?${qs}` : ''}`);
}

export async function createListing(payload: CreateListingPayload): Promise<{ ok: boolean; listing_id: string }> {
  return apiPost('/market/listings', payload);
}

export async function createOrder(payload: {
  order_type: 'buy' | 'sell';
  trader_id: string;
  listing_id?: string;
  strategy_type?: string;
  price: number;
  quantity?: number;
  min_sharpe?: number;
}): Promise<{ ok: boolean; order_id: string }> {
  return apiPost('/market/orders', payload);
}

// ============================================================
// Ecosystem (legacy - keep for EvoMap page compatibility)
// ============================================================

const LEGACY_API_PORTS = [8891, 8889];

async function tryFetch(path: string): Promise<Response> {
  const isBrowser = typeof window !== 'undefined';

  for (const port of LEGACY_API_PORTS) {
    try {
      const url = isBrowser
        ? `/api/proxy${path.replace('/api', '')}`
        : `http://localhost:${port}${path}`;
      const res = await fetch(url, { cache: 'no-store' });
      if (res.ok) return res;
    } catch {
      continue;
    }
  }

  for (const port of LEGACY_API_PORTS) {
    try {
      const res = await fetch(`http://localhost:${port}${path}`, { cache: 'no-store' });
      if (res.ok) return res;
    } catch {
      continue;
    }
  }

  throw new Error(`Failed to fetch ${path} from any API port`);
}

export interface EcosystemNode {
  id: string;
  name: string;
  formula: string;
  generation: number;
  score: number;
  status: string;
  trust_tier?: number;
}

export interface EcosystemLink {
  source: string;
  target: string;
  relation: string;
  shared_count?: number;
}

export interface EcosystemStats {
  total_genes: number;
  max_generation: number;
  avg_sharpe: number;
  top_agent_score?: number;
  negentropy_saved_compute?: number;
  shannon_diversity?: number;
}

export interface EcosystemData {
  nodes: EcosystemNode[];
  links: EcosystemLink[];
  stats: EcosystemStats;
}

export async function fetchEcosystemData(): Promise<EcosystemData> {
  const res = await tryFetch('/api/ecosystem');
  return res.json();
}

export async function fetchStats(): Promise<EcosystemStats> {
  const res = await tryFetch('/api/stats');
  return res.json();
}
