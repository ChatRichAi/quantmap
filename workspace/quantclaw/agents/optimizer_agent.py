#!/usr/bin/env python3
"""
Optimizer agent:
- fetches validated genes
- runs RL parameter optimization
- submits optimized child genes
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

AGENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = AGENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from evolution_ecosystem import Gene
from rl_parameter_optimizer import RLParameterOptimizer

from base_agent import AgentConfig, BaseAgent, common_parser


class OptimizerAgent(BaseAgent):
    def _to_gene(self, payload: Dict[str, Any]) -> Gene:
        return Gene.from_gep(payload)

    def run_once(self) -> Dict[str, Any]:
        genes = self.get("/genes", {"limit": 20}).get("items", [])
        validated = [g for g in genes if g.get("validation", {}).get("status") == "validated"]
        if not validated:
            return {"status": "idle"}

        base_gene = self._to_gene(validated[0])
        optimizer = RLParameterOptimizer(base_gene)
        best = optimizer.optimize(iterations=3)
        if not best:
            return {"status": "no_improvement", "base_gene": base_gene.gene_id}

        variant, reward, metrics = best[0]
        submit = self.post(
            "/genes",
            {
                "gene_id": variant.gene_id,
                "name": variant.name,
                "description": variant.description,
                "formula": variant.formula,
                "parameters": variant.parameters,
                "source": "mutation",
                "author": self.config.agent_id,
                "parent_gene_id": base_gene.gene_id,
                "generation": base_gene.generation + 1,
            },
        )
        return {
            "status": "optimized",
            "base_gene": base_gene.gene_id,
            "new_gene": submit.get("gene_id"),
            "reward": reward,
            "metrics": metrics,
        }


def main() -> None:
    parser = common_parser("Quant EvoMap Optimizer Agent")
    args = parser.parse_args()
    cfg = AgentConfig(agent_id=args.agent_id, role="optimizer", api_base=args.api_base, poll_interval=args.poll_interval)
    agent = OptimizerAgent(cfg)
    if args.once:
        print(agent.run_once())
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
