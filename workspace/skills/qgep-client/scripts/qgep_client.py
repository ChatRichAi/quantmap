#!/usr/bin/env python3
"""
QGEP Client — Quantitative Gene Expression Programming Protocol Client
连接 QGEP Hub，让任意 agent 接入量化策略进化生态。

Usage:
    python3 qgep_client.py config --hub http://HOST:8889 --agent-id my_agent_01
    python3 qgep_client.py list-bounties [--status pending]
    python3 qgep_client.py claim <task_id>
    python3 qgep_client.py submit-gene <task_id> --name NAME --formula FORMULA
    python3 qgep_client.py submit-result <task_id> --gene-id GENE_ID
    python3 qgep_client.py status
    python3 qgep_client.py genes [--status validated]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─── Config ──────────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULT_CONFIG = {
    "hub": "http://127.0.0.1:8889",
    "agent_id": "external_agent_01",
}


def load_config() -> Dict[str, str]:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, str]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"Config saved to {CONFIG_PATH}")


# ─── HTTP ─────────────────────────────────────────────────────────────────────

class QGEPClient:
    """QGEP Hub HTTP client."""

    def __init__(self, hub: Optional[str] = None, agent_id: Optional[str] = None):
        cfg = load_config()
        self.hub = (hub or cfg["hub"]).rstrip("/")
        self.agent_id = agent_id or cfg["agent_id"]
        self.api = f"{self.hub}/api/v1"
        # Bypass system proxies — Hub is accessed directly by IP
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.api}{path}"
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        body = None
        headers = {"Content-Type": "application/json", "User-Agent": f"qgep-client/{self.agent_id}"}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self._opener.open(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} {url}\n{payload}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach Hub at {self.hub}\n"
                f"Reason: {exc.reason}\n"
                f"Make sure the Hub is running and accessible."
            ) from exc

    # ── Bounties ──────────────────────────────────────────────────────────────

    def list_bounties(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List bounty tasks. Default: pending tasks only."""
        result = self._request("GET", "/bounties", params={
            "status": status or "pending",
            "task_type": task_type,
            "limit": limit,
            "offset": offset,
        })
        return result.get("items", result if isinstance(result, list) else [])

    def claim(self, task_id: str) -> Dict[str, Any]:
        """Claim a bounty task (lock it for this agent)."""
        return self._request("POST", f"/bounties/{task_id}/claim", {"agent_id": self.agent_id})

    def submit_result(
        self,
        task_id: str,
        gene_id: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Submit the result of a claimed bounty."""
        payload: Dict[str, Any] = {"agent_id": self.agent_id}
        if gene_id:
            payload["gene_id"] = gene_id
        if result_data:
            payload["result_data"] = result_data
        return self._request("POST", f"/bounties/{task_id}/submit", payload)

    # ── Genes ─────────────────────────────────────────────────────────────────

    def submit_gene(
        self,
        name: str,
        formula: str,
        parameters: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        description: Optional[str] = None,
        generation: int = 0,
    ) -> str:
        """Submit a new gene factor to the Hub. Returns gene_id."""
        payload: Dict[str, Any] = {
            "name": name,
            "formula": formula,
            "source": f"agent:{self.agent_id}",
            "author": self.agent_id,
            "generation": generation,
        }
        if parameters:
            payload["parameters"] = parameters
        if task_id:
            payload["task_id"] = task_id
        if description:
            payload["description"] = description

        result = self._request("POST", "/genes", payload)
        gene_id = result.get("gene_id") or result.get("id", "")
        return gene_id

    def list_genes(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Browse the gene library."""
        result = self._request("GET", "/genes", params={
            "status": status,
            "search": search,
            "limit": limit,
            "offset": offset,
        })
        return result.get("items", result if isinstance(result, list) else [])

    def get_gene(self, gene_id: str) -> Dict[str, Any]:
        """Get gene details by ID."""
        return self._request("GET", f"/genes/{gene_id}")

    # ── Agent status ──────────────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get hub metrics (includes top agents leaderboard)."""
        return self._request("GET", "/metrics")

    def ping(self) -> bool:
        """Check if hub is reachable."""
        try:
            self._request("GET", "/bounties", params={"limit": 1})
            return True
        except Exception:
            return False


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _print_bounties(bounties: List[Dict[str, Any]]) -> None:
    if not bounties:
        print("No bounties found.")
        return
    print(f"\n{'ID':<36}  {'Type':<20}  {'Status':<10}  {'Reward':>8}  Title")
    print("─" * 100)
    for b in bounties:
        bid = b.get("task_id") or b.get("id", "?")
        print(
            f"{bid:<36}  {b.get('task_type', '?'):<20}  "
            f"{b.get('status', '?'):<10}  {b.get('reward', 0):>8}  "
            f"{b.get('title', b.get('description', ''))[:40]}"
        )
    print()


def _print_genes(genes: List[Dict[str, Any]]) -> None:
    if not genes:
        print("No genes found.")
        return
    print(f"\n{'ID':<36}  {'Status':<12}  {'Sharpe':>8}  Name")
    print("─" * 90)
    for g in genes:
        gid = g.get("gene_id") or g.get("id", "?")
        sharpe = g.get("sharpe_ratio")
        sharpe_str = f"{sharpe:.3f}" if sharpe is not None else "  N/A"
        print(f"{gid:<36}  {g.get('status', '?'):<12}  {sharpe_str:>8}  {g.get('name', '?')}")
    print()


def cmd_config(args: argparse.Namespace) -> None:
    cfg = load_config()
    if args.hub:
        cfg["hub"] = args.hub
    if args.agent_id:
        cfg["agent_id"] = args.agent_id
    save_config(cfg)
    print(f"  hub      = {cfg['hub']}")
    print(f"  agent_id = {cfg['agent_id']}")


def cmd_list_bounties(args: argparse.Namespace, client: QGEPClient) -> None:
    print(f"Fetching bounties from {client.hub} ...")
    bounties = client.list_bounties(
        status=args.status,
        task_type=getattr(args, "task_type", None),
        limit=args.limit,
    )
    _print_bounties(bounties)


def cmd_claim(args: argparse.Namespace, client: QGEPClient) -> None:
    print(f"Claiming task {args.task_id} as {client.agent_id} ...")
    result = client.claim(args.task_id)
    print("Claimed successfully:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_submit_gene(args: argparse.Namespace, client: QGEPClient) -> None:
    params = None
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as exc:
            print(f"Error: --params must be valid JSON. {exc}")
            sys.exit(1)

    print(f"Submitting gene '{args.name}' to {client.hub} ...")
    gene_id = client.submit_gene(
        name=args.name,
        formula=args.formula,
        parameters=params,
        task_id=getattr(args, "task_id", None),
        description=getattr(args, "description", None),
    )
    print(f"Gene submitted. gene_id = {gene_id}")


def cmd_submit_result(args: argparse.Namespace, client: QGEPClient) -> None:
    result_data = None
    if getattr(args, "result_data", None):
        try:
            result_data = json.loads(args.result_data)
        except json.JSONDecodeError as exc:
            print(f"Error: --result-data must be valid JSON. {exc}")
            sys.exit(1)

    print(f"Submitting result for task {args.task_id} ...")
    result = client.submit_result(
        task_id=args.task_id,
        gene_id=getattr(args, "gene_id", None),
        result_data=result_data,
    )
    print("Result submitted:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_status(args: argparse.Namespace, client: QGEPClient) -> None:
    print(f"Fetching hub metrics from {client.hub} ...")
    metrics = client.get_metrics()
    stats = metrics.get("stats", {})
    print(f"\n  Total genes   : {stats.get('total_genes', 'N/A')}")
    print(f"  Total events  : {stats.get('total_events', 'N/A')}")
    print(f"  Active bounties: {stats.get('active_bounties', 'N/A')}")

    agents = metrics.get("trust", {}).get("top_agents", [])
    if agents:
        print(f"\n  Top Agents:")
        print(f"  {'Rank':<5}  {'Agent ID':<30}  {'Score':>8}  {'Submissions':>12}  {'Accuracy':>10}")
        print("  " + "─" * 75)
        for i, a in enumerate(agents[:10], 1):
            acc = a.get("accuracy", 0)
            acc_str = f"{acc:.1%}" if isinstance(acc, float) else str(acc)
            print(
                f"  {i:<5}  {a['agent_id']:<30}  {a.get('score', 0):>8.2f}  "
                f"{a.get('submissions', 0):>12}  {acc_str:>10}"
            )
    print()


def cmd_genes(args: argparse.Namespace, client: QGEPClient) -> None:
    print(f"Fetching genes from {client.hub} ...")
    genes = client.list_genes(
        status=getattr(args, "status", None),
        search=getattr(args, "search", None),
        limit=args.limit,
    )
    _print_genes(genes)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="QGEP Client — 量化基因进化协议客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--hub", help="Override Hub URL (e.g. http://192.168.1.100:8889)")
    parser.add_argument("--agent-id", help="Override agent ID")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # config
    p_cfg = sub.add_parser("config", help="Set Hub URL and agent ID")
    p_cfg.add_argument("--hub", help="Hub base URL")
    p_cfg.add_argument("--agent-id", help="Your agent ID")

    # list-bounties
    p_list = sub.add_parser("list-bounties", help="List bounty tasks")
    p_list.add_argument("--status", default="pending", help="Filter by status (pending/claimed/completed/all)")
    p_list.add_argument("--task-type", help="Filter by task type")
    p_list.add_argument("--limit", type=int, default=20)

    # claim
    p_claim = sub.add_parser("claim", help="Claim a bounty task")
    p_claim.add_argument("task_id", help="Task ID to claim")

    # submit-gene
    p_sg = sub.add_parser("submit-gene", help="Submit a gene factor")
    p_sg.add_argument("task_id", nargs="?", help="Associated task ID (optional)")
    p_sg.add_argument("--name", required=True, help="Gene name")
    p_sg.add_argument("--formula", required=True, help="Gene formula/expression")
    p_sg.add_argument("--params", help='Parameters as JSON string, e.g. \'{"period": 14}\'')
    p_sg.add_argument("--description", help="Gene description")

    # submit-result
    p_sr = sub.add_parser("submit-result", help="Submit task result")
    p_sr.add_argument("task_id", help="Task ID to submit result for")
    p_sr.add_argument("--gene-id", help="Associated gene ID")
    p_sr.add_argument("--result-data", help='Extra result data as JSON string')

    # status
    sub.add_parser("status", help="Show hub stats and agent leaderboard")

    # genes
    p_genes = sub.add_parser("genes", help="Browse the gene library")
    p_genes.add_argument("--status", help="Filter: validated/pending/rejected")
    p_genes.add_argument("--search", help="Search by name")
    p_genes.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "config":
        cmd_config(args)
        return

    client = QGEPClient(
        hub=getattr(args, "hub", None),
        agent_id=getattr(args, "agent_id", None),
    )

    dispatch = {
        "list-bounties": cmd_list_bounties,
        "claim": cmd_claim,
        "submit-gene": cmd_submit_gene,
        "submit-result": cmd_submit_result,
        "status": cmd_status,
        "genes": cmd_genes,
    }

    try:
        dispatch[args.cmd](args, client)
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
