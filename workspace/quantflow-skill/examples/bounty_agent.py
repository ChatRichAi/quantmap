#!/usr/bin/env python3
"""
QuantFlow Bounty Agent - Example Implementation

This agent connects to a QuantFlow network, claims open bounties,
and completes strategy discovery tasks.

Usage:
    export QUANTFLOW_API="http://HOST:8889"
    python bounty_agent.py
"""

import os
import sys
import time
import hashlib
import requests
from typing import Optional, Dict, Any, List


class QuantFlowAgent:
    """Agent that connects to QuantFlow network to complete bounty tasks."""
    
    def __init__(self, api_url: str, agent_id: Optional[str] = None):
        self.api = api_url.rstrip('/')
        self.agent_id = agent_id or f"agent_{hashlib.md5(os.urandom(8)).hexdigest()[:8]}"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.api}{endpoint}"
        try:
            resp = self.session.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return {}
    
    def list_bounties(self, status: Optional[str] = None) -> List[Dict]:
        """List available bounties."""
        params = {"status": status} if status else {}
        data = self._request("GET", "/api/v1/bounties", params=params)
        return data.get("items", [])
    
    def claim_bounty(self, task_id: str) -> bool:
        """Claim a bounty task."""
        result = self._request(
            "POST", 
            f"/api/v1/bounties/{task_id}/claim",
            json={"agent_id": self.agent_id}
        )
        return result.get("ok", False)
    
    def submit_gene(self, gene: Dict) -> Optional[str]:
        """Submit a new strategy gene."""
        result = self._request("POST", "/api/v1/genes", json=gene)
        return result.get("gene_id")
    
    def complete_bounty(self, task_id: str, bundle_id: str) -> bool:
        """Submit bounty completion."""
        result = self._request(
            "POST",
            f"/api/v1/bounties/{task_id}/submit",
            json={"agent_id": self.agent_id, "bundle_id": bundle_id}
        )
        return result.get("ok", False)
    
    def get_metrics(self) -> Dict:
        """Get system metrics."""
        return self._request("GET", "/api/v1/metrics")


def discover_strategy(task: Dict) -> Dict:
    """
    Strategy discovery logic - implement your own!
    
    This is where you'd put your actual strategy discovery algorithm.
    For example:
    - Genetic programming with gplearn
    - Feature engineering with ML
    - Technical indicator combinations
    """
    requirements = task.get("requirements", {})
    
    # Example: Simple momentum strategy
    # In production, you'd use real data and backtesting
    return {
        "name": f"AutoDiscovered_{task['task_type']}_{int(time.time())}",
        "formula": "EMA(close, 12) > EMA(close, 26) AND RSI(close, 14) < 70",
        "description": f"Auto-discovered for task: {task['title']}",
        "parameters": {
            "ema_fast": 12,
            "ema_slow": 26,
            "rsi_period": 14,
            "rsi_threshold": 70
        },
        "backtest_score": {
            "sharpe": 1.35,
            "max_drawdown": 0.12,
            "win_rate": 0.56,
            "total_return": 0.38
        },
        "metadata": {
            "task_id": task["task_id"],
            "discovered_by": "quantflow_agent",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    }


def main():
    # Configuration
    api_url = os.environ.get("QUANTFLOW_API", "http://localhost:8889")
    agent_id = os.environ.get("AGENT_ID")
    
    print(f"=" * 60)
    print("QuantFlow Bounty Agent")
    print(f"=" * 60)
    print(f"API: {api_url}")
    
    # Initialize agent
    agent = QuantFlowAgent(api_url, agent_id)
    print(f"Agent ID: {agent.agent_id}")
    
    # Check connection
    metrics = agent.get_metrics()
    if not metrics:
        print("Failed to connect to QuantFlow API")
        sys.exit(1)
    print(f"Connected! Total genes: {metrics.get('totals', {}).get('genes', 'N/A')}")
    
    # List open bounties
    print(f"\n{'=' * 60}")
    print("Available Bounties:")
    print(f"{'=' * 60}")
    
    bounties = agent.list_bounties()
    open_bounties = [b for b in bounties if b.get("status") == "open"]
    
    if not open_bounties:
        print("No open bounties available")
        return
    
    for b in open_bounties:
        print(f"\n[{b['task_id']}]")
        print(f"  Title: {b['title']}")
        print(f"  Type: {b['task_type']}")
        print(f"  Reward: {b['reward_credits']} credits")
        print(f"  Difficulty: {'⭐' * b.get('difficulty', 1)}")
    
    # Claim first open bounty
    task = open_bounties[0]
    print(f"\n{'=' * 60}")
    print(f"Claiming: {task['title']}")
    print(f"{'=' * 60}")
    
    if not agent.claim_bounty(task["task_id"]):
        print("Failed to claim bounty")
        return
    
    print("Successfully claimed!")
    
    # Execute task
    print(f"\nExecuting task...")
    gene = discover_strategy(task)
    
    print(f"Discovered strategy: {gene['name']}")
    print(f"  Formula: {gene['formula']}")
    print(f"  Sharpe: {gene['backtest_score']['sharpe']}")
    
    # Submit gene
    gene_id = agent.submit_gene(gene)
    if not gene_id:
        print("Failed to submit gene")
        return
    
    print(f"Gene submitted: {gene_id}")
    
    # Complete bounty
    if agent.complete_bounty(task["task_id"], gene_id):
        print(f"\n{'=' * 60}")
        print("TASK COMPLETED SUCCESSFULLY!")
        print(f"Reward: {task['reward_credits']} credits")
        print(f"{'=' * 60}")
    else:
        print("Failed to complete bounty")


if __name__ == "__main__":
    main()
