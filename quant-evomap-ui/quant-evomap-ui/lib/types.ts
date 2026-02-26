// ============================================================
// Core Data Types for QuantClaw QGEP Management Console
// ============================================================

export interface Gene {
  gene_id: string;
  name: string;
  description: string;
  formula: string;
  parameters: Record<string, number | string>;
  source: string;
  author: string;
  created_at: string;
  parent_gene_id?: string;
  generation: number;
  lineage?: {
    parent_ids: string[];
    mutation_type: string;
  };
  validation?: {
    status: 'pending' | 'validated' | 'rejected';
    sharpe_ratio?: number;
    max_drawdown?: number;
    win_rate?: number;
    test_symbols?: string[];
    test_period?: string;
  };
  meta?: {
    author: string;
    created_at: string;
    source: string;
    tags?: string[];
    description?: string;
  };
}

export interface GenesResponse {
  items: Gene[];
  count: number;
  limit: number;
  offset: number;
}

export interface Capsule {
  capsule_id: string;
  gene_id: string;
  code: string;
  language: string;
  dependencies: string[];
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  tested: boolean;
  validated: boolean;
  author: string;
  created_at: string;
  validation?: {
    tested: boolean;
    validated: boolean;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
  };
  meta?: {
    author: string;
    created_at: string;
  };
}

export interface CapsulesResponse {
  items: Capsule[];
  count: number;
}

export interface EvolutionEvent {
  event_id: string;
  gene_id: string;
  capsule_id: string;
  event_type: 'created' | 'mutated' | 'tested' | 'deployed' | 'daemon_cycle';
  trigger: string;
  test_data: Record<string, unknown>;
  gdi_score: number;
  meta: {
    author: string;
    timestamp: string;
  };
}

export interface EventsResponse {
  items: EvolutionEvent[];
  count: number;
}

export type BountyStatus = 'pending' | 'claimed' | 'completed' | 'failed' | 'expired';
export type BountyTaskType = 'discover_factor' | 'optimize_strategy' | 'implement_paper';

export interface BountyTask {
  task_id: string;
  title: string;
  description: string;
  task_type: BountyTaskType;
  status: BountyStatus;
  reward_credits: number;
  difficulty: number;
  requirements: Record<string, unknown>;
  claimed_by?: string;
  result_bundle_id?: string;
  created_at: string;
  deadline?: string;
}

export interface BountiesResponse {
  items: BountyTask[];
}

export interface CreateBountyPayload {
  title: string;
  description: string;
  task_type: BountyTaskType;
  reward_credits: number;
  difficulty: number;
  requirements: Record<string, unknown>;
  deadline?: string;
}

export interface AgentReputation {
  agent_id: string;
  score: number;
  submissions: number;
  accepted: number;
  validations: number;
  accuracy: number;
}

export interface MetricsResponse {
  totals: {
    genes: number;
    events: number;
    reused_genes: number;
  };
  negentropy: {
    saved_compute: number;
    shannon_diversity: number;
  };
  trust: {
    top_agents: AgentReputation[];
  };
}

export interface EvolverStatus {
  running: boolean;
  pid: number | null;
  state: Record<string, unknown>;
}

export interface StrategyListing {
  listing_id: string;
  seller_id: string;
  bundle_id: string;
  gene_id: string;
  capsule_id: string;
  title: string;
  description: string;
  strategy_type: string;
  sharpe_ratio: number;
  max_drawdown: number;
  annual_return: number;
  win_rate: number;
  backtest_period: string;
  validation_count: number;
  validator_scores: number[];
  price: number;
  price_model: 'fixed' | 'auction' | 'performance_based';
  license_type: 'one_time' | 'subscription' | 'royalty';
  royalty_rate: number;
  status?: string;
  score?: number;
  views?: number;
  sales_count?: number;
}

export interface ListingsResponse {
  items: StrategyListing[];
  count: number;
}

export interface CreateListingPayload {
  seller_id: string;
  bundle_id: string;
  gene_id: string;
  capsule_id: string;
  title: string;
  description: string;
  strategy_type: string;
  sharpe_ratio: number;
  max_drawdown: number;
  annual_return: number;
  win_rate: number;
  backtest_period: string;
  validation_count: number;
  price: number;
  price_model: string;
  license_type: string;
  royalty_rate?: number;
}

export interface EcosystemStats {
  total_genes: number;
  total_nodes: number;
  total_links: number;
  unique_lineages: number;
  negentropy_saved_compute: number;
  shannon_diversity: number;
  top_agent_score: number;
  timestamp: string;
  // legacy fields from existing api.ts
  max_generation?: number;
  avg_sharpe?: number;
}
