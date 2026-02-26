#!/usr/bin/env python3
"""
Miner agent:
- claims strategy discovery bounties
- discovers candidate genes
- submits genes through API
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

AGENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = AGENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from autonomous_seed_discovery import AutonomousSeedDiscovery
from evolution_ecosystem import Gene

from base_agent import AgentConfig, BaseAgent, common_parser


QUANT_EVOMAP_PROTO_PATH = "/Users/oneday/.openclaw/workspace/quant-evomap-prototype"
if QUANT_EVOMAP_PROTO_PATH not in sys.path:
    sys.path.insert(0, QUANT_EVOMAP_PROTO_PATH)
try:
    from quant_evomap import QuantEvoMap  # type: ignore
except Exception:
    QuantEvoMap = None  # type: ignore


class MinerAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.discovery = AutonomousSeedDiscovery()
        self.quant_evomap = QuantEvoMap() if QuantEvoMap else None

    def _submit_gene(self, gene: Gene) -> Dict[str, Any]:
        payload = gene.to_gep()
        payload["meta"]["author"] = self.config.agent_id
        payload["meta"]["created_at"] = datetime.now().isoformat()
        return self.post("/genes", payload)

    def run_once(self) -> Dict[str, Any]:
        bounty = self.claim_next_bounty(task_type="discover_factor")
        if not bounty:
            bounty = self.claim_next_bounty(task_type="strategy_discovery")
        if not bounty:
            return {"status": "idle"}

        symbol = bounty.get("requirements", {}).get("symbol", "AAPL")

        # Path A: use prototype GP miner if available.
        if self.quant_evomap:
            result = self.quant_evomap.discover_strategy(symbol, save_results=False)
            gene_data = result["gene"]
            submit_result = self.post(
                "/genes",
                {
                    "gene_id": gene_data.get("id", ""),
                    "name": f"GP_{symbol}_{gene_data.get('id', 'gene')}",
                    "description": "Discovered by QuantEvoMap prototype miner",
                    "formula": gene_data.get("expression") or "Close > SMA(20)",
                    "parameters": gene_data.get("params", {}),
                    "source": "seed_discovery",
                    "author": self.config.agent_id,
                    "generation": gene_data.get("generation", 0),
                },
            )
            self.post(
                f"/bounties/{bounty['task_id']}/submit",
                {"agent_id": self.config.agent_id, "bundle_id": f"bundle_{submit_result['gene_id']}"},
            )
            return {"status": "completed", "task_id": bounty["task_id"], "gene_id": submit_result["gene_id"]}

        # Path B: fallback to autonomous seed discovery engine.
        seeds = self.discovery.discover_seeds(symbols=[symbol], n_seeds=1)
        if not seeds:
            return {"status": "no_seed_found", "task_id": bounty["task_id"]}
        submit = self._submit_gene(seeds[0])
        self.post(
            f"/bounties/{bounty['task_id']}/submit",
            {"agent_id": self.config.agent_id, "bundle_id": f"bundle_{submit['gene_id']}"},
        )
        return {"status": "completed", "task_id": bounty["task_id"], "gene_id": submit["gene_id"]}


def main() -> None:
    parser = common_parser("Quant EvoMap Miner Agent")
    args = parser.parse_args()
    cfg = AgentConfig(agent_id=args.agent_id, role="miner", api_base=args.api_base, poll_interval=args.poll_interval)
    agent = MinerAgent(cfg)
    if args.once:
        print(agent.run_once())
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
