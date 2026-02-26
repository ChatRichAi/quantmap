#!/usr/bin/env python3
"""
Validator agent:
- fetches pending genes
- runs independent validation
- submits capsule with validation result
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

AGENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = AGENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from evolution_ecosystem import Gene
from factor_backtest_validator import FactorValidator

from base_agent import AgentConfig, BaseAgent, common_parser


class ValidatorAgent(BaseAgent):
    def __init__(self, config: AgentConfig, db_path: str = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"):
        super().__init__(config)
        self.validator = FactorValidator(db_path=db_path)

    def _to_gene(self, payload: Dict[str, Any]) -> Gene:
        return Gene.from_gep(payload)

    def _submit_capsule(self, gene: Gene, results: List[Any]) -> Dict[str, Any]:
        if results:
            sharpe = sum(r.sharpe_ratio for r in results) / len(results)
            max_dd = sum(r.max_drawdown for r in results) / len(results)
            win_rate = sum(r.win_rate for r in results) / len(results)
            validated = any(r.passed for r in results)
        else:
            sharpe = 0.0
            max_dd = 1.0
            win_rate = 0.0
            validated = False

        capsule_payload = {
            "capsule_id": "",
            "gene_id": gene.gene_id,
            "code": f"# Auto capsule by {self.config.agent_id}\n# Formula: {gene.formula}\n",
            "language": "python",
            "dependencies": ["pandas", "numpy"],
            "validation": {
                "tested": True,
                "validated": validated,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "win_rate": win_rate,
            },
            "meta": {
                "author": self.config.agent_id,
                "created_at": datetime.now().isoformat(),
            },
        }
        return self.post("/capsules", capsule_payload)

    def run_once(self) -> Dict[str, Any]:
        genes = self.get("/genes", {"limit": 20}).get("items", [])
        pending = [g for g in genes if g.get("validation", {}).get("status") == "pending"]
        if not pending:
            return {"status": "idle"}

        target = pending[0]
        gene = self._to_gene(target)
        results = self.validator.validate_gene(
            gene,
            symbols=["AAPL", "MSFT"],
            start_date="2022-01-01",
            end_date="2024-12-31",
        )
        capsule = self._submit_capsule(gene, results)
        return {
            "status": "validated",
            "gene_id": gene.gene_id,
            "capsule_id": capsule.get("capsule_id"),
            "result_count": len(results),
        }


def main() -> None:
    parser = common_parser("Quant EvoMap Validator Agent")
    args = parser.parse_args()
    cfg = AgentConfig(agent_id=args.agent_id, role="validator", api_base=args.api_base, poll_interval=args.poll_interval)
    agent = ValidatorAgent(cfg)
    if args.once:
        print(agent.run_once())
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
