#!/usr/bin/env python3
"""
QGEP Client — Quantitative Gene Expression Programming Protocol Client
连接 QGEP Hub，让任意 agent 接入量化策略进化生态。

Usage:
    qgep config --hub http://HOST:8889 --agent-id my_agent_01
    qgep hello                             # A2A 注册节点
    qgep list-bounties [--status pending]  # 查看任务
    qgep claim <task_id>                   # 认领任务
    qgep submit-gene <task_id> --name NAME --formula EXPR
    qgep submit-result <task_id> --gene-id GENE_ID
    qgep nodes                             # 节点监控
    qgep status                            # 排行榜
    qgep genes [--status validated]        # 基因库
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─── ANSI Colors ──────────────────────────────────────────────────────────────

GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
RESET  = '\033[0m'

def _ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET} {msg}")
def _info(msg: str) -> None: print(f"  {DIM}→{RESET} {msg}")
def _warn(msg: str) -> None: print(f"  {YELLOW}⚠{RESET} {msg}")
def _err(msg: str)  -> None: print(f"  {RED}✗{RESET} {msg}", file=sys.stderr)

def _header(title: str, sub: str = "") -> None:
    print(f"\n{BOLD}{CYAN}{title}{RESET}")
    if sub:
        print(f"  {DIM}{sub}{RESET}")
    print(f"  {'─' * 66}")

def _sep() -> None:
    print(f"  {'─' * 66}")

def _status_color(status: str) -> str:
    colors = {
        "pending":   YELLOW,
        "open":      YELLOW,
        "claimed":   CYAN,
        "completed": GREEN,
        "failed":    RED,
        "expired":   DIM,
        "alive":     GREEN,
        "dormant":   YELLOW,
        "offline":   RED,
        "validated": GREEN,
        "rejected":  RED,
    }
    c = colors.get(status.lower(), RESET)
    return f"{c}{status}{RESET}"

def _time_ago(iso: Optional[str]) -> str:
    """Convert ISO timestamp to human-friendly 'X min ago'."""
    if not iso:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = (now - dt).total_seconds()
        if diff < 60:
            return "just now"
        if diff < 3600:
            return f"{int(diff / 60)} min ago"
        if diff < 86400:
            return f"{int(diff / 3600)} hr ago"
        return f"{int(diff / 86400)} days ago"
    except Exception:
        return iso[:16] if iso else "unknown"


# ─── Config ───────────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent.parent / "config.json"

DEFAULT_CONFIG: Dict[str, str] = {
    "hub":          "http://127.0.0.1:8889",
    "agent_id":     "external_agent_01",
    "llm_provider": "",
    "llm_api_key":  "",
    "llm_model":    "",
    "llm_base_url": "",
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


# ─── HTTP Client ──────────────────────────────────────────────────────────────

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
                f"  Reason: {exc.reason}\n"
                f"  Make sure the Hub is running and accessible."
            ) from exc

    # ── Bounties ──────────────────────────────────────────────────────────────

    def list_bounties(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        result = self._request("GET", "/bounties", params={
            "status": status or "open",
            "task_type": task_type,
            "limit": limit,
            "offset": offset,
        })
        return result.get("items", result if isinstance(result, list) else [])

    def claim(self, task_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/bounties/{task_id}/claim", {"agent_id": self.agent_id})

    def submit_result(
        self,
        task_id: str,
        gene_id: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"agent_id": self.agent_id}
        payload["bundle_id"] = gene_id or f"result_{task_id}"
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
        return result.get("gene_id") or result.get("id", "")

    def list_genes(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        result = self._request("GET", "/genes", params={
            "status": status,
            "search": search,
            "limit": limit,
            "offset": offset,
        })
        return result.get("items", result if isinstance(result, list) else [])

    def get_gene(self, gene_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/genes/{gene_id}")

    # ── A2A Protocol ──────────────────────────────────────────────────────────

    def _a2a_request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.hub}{path}"
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
            raise RuntimeError(f"Cannot reach Hub at {self.hub}\nReason: {exc.reason}") from exc

    def a2a_hello(self) -> Dict[str, Any]:
        node_id = self.agent_id if self.agent_id.startswith("node_") else f"node_{self.agent_id}"
        payload = {
            "sender_id": node_id,
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": "hello",
            "message_id": f"msg_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"agent_id": self.agent_id, "version": "qgep-client/1.0"},
        }
        return self._a2a_request("POST", "/a2a/hello", payload)

    def a2a_heartbeat(self) -> Dict[str, Any]:
        node_id = self.agent_id if self.agent_id.startswith("node_") else f"node_{self.agent_id}"
        payload = {
            "sender_id": node_id,
            "protocol": "gep-a2a",
            "protocol_version": "1.0.0",
            "message_type": "heartbeat",
            "message_id": f"msg_{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        return self._a2a_request("POST", "/a2a/heartbeat", payload)

    def a2a_nodes(self) -> Dict[str, Any]:
        return self._a2a_request("GET", "/a2a/nodes")

    def get_metrics(self) -> Dict[str, Any]:
        return self._request("GET", "/metrics")

    def ping(self) -> bool:
        try:
            self._request("GET", "/bounties", params={"limit": 1})
            return True
        except Exception:
            return False


# ─── CLI Commands ─────────────────────────────────────────────────────────────

def cmd_config(args: argparse.Namespace) -> None:
    cfg = load_config()
    if getattr(args, "hub", None):
        cfg["hub"] = args.hub
    if getattr(args, "agent_id", None):
        cfg["agent_id"] = args.agent_id
    save_config(cfg)
    _ok("Configuration saved")
    print(f"\n    hub      = {CYAN}{cfg['hub']}{RESET}")
    print(f"    agent_id = {GREEN}{cfg['agent_id']}{RESET}\n")


def cmd_hello(args: argparse.Namespace, client: QGEPClient) -> None:
    node_id = client.agent_id if client.agent_id.startswith("node_") else f"node_{client.agent_id}"
    _info(f"Registering {BOLD}{node_id}{RESET} with Hub {DIM}{client.hub}{RESET} ...")
    result = client.a2a_hello()
    print()
    _ok(f"{GREEN}{BOLD}Node registered!{RESET}")
    print()
    print(f"    Node ID    : {CYAN}{result.get('your_node_id', node_id)}{RESET}")
    print(f"    Claim Code : {BOLD}{result.get('claim_code', 'N/A')}{RESET}")
    print(f"    Credits    : {GREEN}{result.get('credit_balance', 500)}{RESET}")
    print(f"    Status     : {_status_color(result.get('survival_status', 'alive'))}")
    print()
    _info(f"Next: {CYAN}qgep list-bounties{RESET}  to see available tasks")
    print()


def cmd_heartbeat(args: argparse.Namespace, client: QGEPClient) -> None:
    node_id = client.agent_id if client.agent_id.startswith("node_") else f"node_{client.agent_id}"
    result = client.a2a_heartbeat()
    status = result.get("status", "ok")
    _ok(f"Heartbeat sent  ({CYAN}{node_id}{RESET} → {_status_color('alive' if status == 'ok' else status)})")


def cmd_nodes(args: argparse.Namespace, client: QGEPClient) -> None:
    _info(f"Fetching nodes from {DIM}{client.hub}{RESET} ...")
    result = client.a2a_nodes()
    nodes = result.get("nodes", [])

    alive_count   = sum(1 for n in nodes if n.get("survival_status") == "alive")
    dormant_count = sum(1 for n in nodes if n.get("survival_status") == "dormant")

    _header(
        f"Registered Nodes  ({len(nodes)} total)",
        f"alive={alive_count}  dormant={dormant_count}"
    )

    if not nodes:
        print(f"  {DIM}No nodes registered yet. Run: qgep hello{RESET}\n")
        return

    for n in nodes:
        status = n.get("survival_status", "unknown")
        dot_color = GREEN if status == "alive" else (YELLOW if status == "dormant" else RED)
        node_id   = n.get("node_id", "?")
        credits   = n.get("credit_balance", 0)
        last_seen = _time_ago(n.get("last_heartbeat"))
        is_me     = node_id == f"node_{client.agent_id}" or node_id == client.agent_id
        me_tag    = f"  {DIM}← you{RESET}" if is_me else ""
        print(
            f"  {dot_color}●{RESET} {BOLD}{node_id:<42}{RESET}"
            f"  {_status_color(status):<10}  {GREEN}{credits:>4} cr{RESET}"
            f"  {DIM}last seen:{RESET} {last_seen}{me_tag}"
        )

    _sep()
    print(
        f"  {GREEN}alive={alive_count}{RESET}  "
        f"{YELLOW}dormant={dormant_count}{RESET}  "
        f"{DIM}(heartbeat timeout: 45 min){RESET}"
    )
    print()


def cmd_list_bounties(args: argparse.Namespace, client: QGEPClient) -> None:
    status = getattr(args, "status", "pending")
    _info(f"Fetching bounties {DIM}[status: {status}]{RESET} from {DIM}{client.hub}{RESET} ...")
    bounties = client.list_bounties(
        status=status,
        task_type=getattr(args, "task_type", None),
        limit=args.limit,
    )

    _header(
        f"Bounty Tasks  [status: {_status_color(status)}]",
        f"{len(bounties)} found"
    )

    if not bounties:
        print(f"  {DIM}No bounties with status '{status}'.{RESET}")
        print(f"  Try: {CYAN}qgep list-bounties --status pending{RESET}\n")
        return

    print(f"  {DIM}{'ID':<38}  {'Type':<22}  {'Reward':>6}  Title{RESET}")
    for b in bounties:
        bid     = b.get("task_id") or b.get("id", "?")
        btype   = b.get("task_type", "?")
        reward  = b.get("reward_credits") or b.get("reward", 0)
        title   = b.get("title", b.get("description", ""))[:38]
        reward_str = f"{GREEN}{reward:>6}{RESET}" if reward > 0 else f"{DIM}{reward:>6}{RESET}"
        print(f"  {CYAN}{bid:<38}{RESET}  {btype:<22}  {reward_str}  {title}")

    _sep()
    if bounties:
        first_id = bounties[0].get("task_id") or bounties[0].get("id", "?")
        print(f"  {DIM}Run: {RESET}{CYAN}qgep claim {first_id}{RESET}")
    print()


def cmd_claim(args: argparse.Namespace, client: QGEPClient) -> None:
    _info(f"Claiming {BOLD}{args.task_id}{RESET} as {CYAN}{client.agent_id}{RESET} ...")
    client.claim(args.task_id)
    print()
    _ok(f"{GREEN}{BOLD}Task claimed!{RESET}  (agent: {CYAN}{client.agent_id}{RESET})")
    print()
    print(f"  {DIM}Next step:{RESET}")
    print(f"    {CYAN}qgep submit-gene {args.task_id}{RESET} {DIM}--name <name> --formula <expr>{RESET}")
    print()


def cmd_submit_gene(args: argparse.Namespace, client: QGEPClient) -> None:
    params = None
    if getattr(args, "params", None):
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as exc:
            _err(f"--params must be valid JSON: {exc}")
            sys.exit(1)

    task_id = getattr(args, "task_id", None)
    _info(f"Submitting gene: {BOLD}{args.name}{RESET} ...")

    gene_id = client.submit_gene(
        name=args.name,
        formula=args.formula,
        parameters=params,
        task_id=task_id,
        description=getattr(args, "description", None),
    )

    print()
    _ok(f"{GREEN}{BOLD}Gene submitted!{RESET}")
    print()
    print(f"    Gene ID : {CYAN}{gene_id}{RESET}")
    print(f"    Formula : {DIM}{args.formula[:60]}{RESET}")
    if task_id:
        print(f"    Task    : {task_id}")
    print()
    if task_id and gene_id:
        print(f"  {DIM}Next step:{RESET}")
        print(f"    {CYAN}qgep submit-result {task_id} --gene-id {gene_id}{RESET}")
    print()


def cmd_submit_result(args: argparse.Namespace, client: QGEPClient) -> None:
    result_data = None
    if getattr(args, "result_data", None):
        try:
            result_data = json.loads(args.result_data)
        except json.JSONDecodeError as exc:
            _err(f"--result-data must be valid JSON: {exc}")
            sys.exit(1)

    gene_id = getattr(args, "gene_id", None)
    _info(f"Submitting result for {BOLD}{args.task_id}{RESET} ...")

    client.submit_result(
        task_id=args.task_id,
        gene_id=gene_id,
        result_data=result_data,
    )

    print()
    _ok(f"{GREEN}{BOLD}Task completed!{RESET}")
    print()
    print(f"    Task ID : {CYAN}{args.task_id}{RESET}")
    if gene_id:
        print(f"    Gene ID : {gene_id}")
    print(f"    Agent   : {CYAN}{client.agent_id}{RESET}")
    print()
    _info(f"Check leaderboard: {CYAN}qgep status{RESET}")
    print()


def cmd_status(args: argparse.Namespace, client: QGEPClient) -> None:
    _info(f"Fetching metrics from {DIM}{client.hub}{RESET} ...")
    metrics = client.get_metrics()
    totals  = metrics.get("totals", metrics.get("stats", {}))
    neg     = metrics.get("negentropy", {})

    _header("Hub Metrics")
    total_genes    = totals.get("genes",    totals.get("total_genes",    "N/A"))
    total_events   = totals.get("events",   totals.get("total_events",   "N/A"))
    reused         = totals.get("reused_genes", "N/A")
    diversity      = neg.get("shannon_diversity", None)

    print(f"  Total Genes     : {BOLD}{total_genes}{RESET}")
    print(f"  Total Events    : {BOLD}{total_events}{RESET}")
    print(f"  Reused Genes    : {BOLD}{reused}{RESET}")
    if diversity is not None:
        print(f"  Gene Diversity  : {BOLD}{diversity:.4f}{RESET}")

    agents = metrics.get("trust", {}).get("top_agents", [])
    if agents:
        print()
        _header("Top Agents")
        print(f"  {DIM}{'Rank':<5}  {'Agent ID':<32}  {'Score':>8}  {'Submissions':>11}  {'Accuracy':>9}{RESET}")
        for i, a in enumerate(agents[:10], 1):
            acc = a.get("accuracy", 0)
            acc_str = f"{acc:.1%}" if isinstance(acc, float) else str(acc)
            rank_str = f"#{i}"
            is_me = a.get("agent_id") == client.agent_id
            me_tag = f"  {DIM}← you{RESET}" if is_me else ""
            agent_col = f"{GREEN}{a['agent_id']}{RESET}" if is_me else a["agent_id"]
            print(
                f"  {CYAN}{rank_str:<5}{RESET}  {agent_col:<32}  "
                f"{a.get('score', 0):>8.1f}  {a.get('submissions', 0):>11}  {acc_str:>9}{me_tag}"
            )
        _sep()
    print()


def cmd_genes(args: argparse.Namespace, client: QGEPClient) -> None:
    _info(f"Fetching genes from {DIM}{client.hub}{RESET} ...")
    genes = client.list_genes(
        status=getattr(args, "status", None),
        search=getattr(args, "search", None),
        limit=args.limit,
    )

    status_filter = getattr(args, "status", None) or "all"
    _header(f"Gene Library  [status: {_status_color(status_filter)}]", f"{len(genes)} found")

    if not genes:
        print(f"  {DIM}No genes found.{RESET}\n")
        return

    print(f"  {DIM}{'ID':<18}  {'Status':<12}  {'Sharpe':>8}  Name{RESET}")
    for g in genes:
        gid    = (g.get("gene_id") or g.get("id", "?"))[:16]
        status = g.get("status", "?")
        sharpe = g.get("sharpe_ratio")
        sharpe_str = f"{sharpe:>8.3f}" if sharpe is not None else f"{'N/A':>8}"
        print(
            f"  {CYAN}{gid:<18}{RESET}  {_status_color(status):<12}  "
            f"{sharpe_str}  {g.get('name', '?')}"
        )
    _sep()
    print()


def cmd_setup(args: argparse.Namespace, client: QGEPClient) -> None:
    """Interactive setup wizard — run after install or anytime to reconfigure."""
    _print_quantmap_banner()
    print(f"\n  {BOLD}Setup Wizard{RESET}  {DIM}— 配置你的 QGEP Agent{RESET}")
    print(f"  {DIM}{'━' * 62}{RESET}\n")
    work_mode = "manual"  # default, updated in step 4

    cfg = load_config()

    # ── Step 1: Register Node ────────────────────────────────────────────────
    print(f"{CYAN}{BOLD}[1/6] Register Agent Node{RESET}")
    try:
        result = client.a2a_hello()
        node_id    = result.get("node_id", client.agent_id)
        credits    = result.get("credits", 500)
        claim_code = result.get("claim_code", "—")
        _ok(f"{GREEN}{BOLD}Node registered!{RESET}")
        print(f"\n    Node ID    : {CYAN}{node_id}{RESET}")
        print(f"    Claim Code : {BOLD}{claim_code}{RESET}")
        print(f"    Credits    : {GREEN}{credits}{RESET}")
    except Exception as exc:
        _warn(f"Could not reach Hub: {exc}")
        _info(f"You can still configure LLM. Run {CYAN}qgep hello{RESET} after Hub is started.")
    print()

    # ── Step 2: LLM Provider ─────────────────────────────────────────────────
    print(f"{CYAN}{BOLD}[2/6] Configure LLM Provider{RESET}")
    providers = [
        ("openai",    "gpt-4o",                        True),
        ("anthropic", "claude-sonnet-4-20250514",       True),
        ("deepseek",  "deepseek-chat",                  True),
        ("ollama",    "llama3",                         False),
        ("skip",      "",                               False),
    ]
    print(f"\n  Select your LLM provider:")
    labels = ["OpenAI     (gpt-4o)", "Anthropic  (claude-sonnet-4-20250514)",
              "DeepSeek   (deepseek-chat)", "Ollama     (local, no key needed)", "Skip       (configure later)"]
    for i, label in enumerate(labels, 1):
        print(f"    {DIM}{i}){RESET} {label}")
    print()

    try:
        choice_str = input(f"  {BOLD}>{RESET} ").strip()
        choice = int(choice_str) if choice_str.isdigit() else 5
        choice = max(1, min(5, choice))
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {DIM}Setup skipped. Run {CYAN}qgep setup{RESET}{DIM} anytime to reconfigure.{RESET}\n")
        return

    provider, default_model, needs_key = providers[choice - 1]

    if provider != "skip":
        cfg["llm_provider"] = provider
        cfg["llm_model"]    = default_model

        if needs_key:
            print(f"\n  {DIM}Enter your {provider} API key:{RESET}", end=" ", flush=True)
            try:
                api_key = getpass.getpass("")
            except (KeyboardInterrupt, EOFError):
                api_key = ""
            if api_key.strip():
                cfg["llm_api_key"] = api_key.strip()
                _ok("API key saved")
            else:
                _warn("Empty key — skipped")
        else:
            cfg["llm_api_key"] = ""
            _ok(f"{provider} configured (no key required)")

        save_config(cfg)
    else:
        _info("LLM skipped — configure later with: qgep config")
    print()

    # ── Step 3: Test Connections ─────────────────────────────────────────────
    print(f"{CYAN}{BOLD}[3/6] Testing Connections{RESET}\n")

    # Hub
    print(f"  {DIM}→{RESET} Hub connection    ...", end=" ", flush=True)
    try:
        client.ping()
        tasks = client.list_bounties(status="pending", limit=5)
        print(f"{GREEN}✓{RESET}")
        _ok(f"Available tasks: {GREEN}{len(tasks)} pending{RESET}")
    except Exception:
        print(f"{YELLOW}⚠{RESET}")
        _warn("Hub not reachable — start the Hub and run `qgep hello`")

    # LLM
    if provider not in ("skip", "") and cfg.get("llm_api_key"):
        print(f"  {DIM}→{RESET} LLM API key       ...", end=" ", flush=True)
        ok_llm, msg = _test_llm_key(
            cfg["llm_provider"],
            cfg["llm_api_key"],
            cfg["llm_model"],
            cfg.get("llm_base_url", ""),
        )
        if ok_llm:
            print(f"{GREEN}✓{RESET}")
        else:
            print(f"{RED}✗{RESET}")
            _warn(f"LLM test failed: {msg}")
    print()

    # ── Step 4: Choose Work Mode ─────────────────────────────────────────────
    print(f"{CYAN}{BOLD}[4/6] Choose Work Mode{RESET}\n")
    print(f"  {DIM}1){RESET}  {BOLD}手动接单模式{RESET}  {DIM}— 自己查看任务、选择接单、提交结果（推荐新手）{RESET}")
    print(f"  {DIM}2){RESET}  {BOLD}自动抢单模式{RESET}  {DIM}— Agent 后台全自动轮询、接单、执行、提交（无人值守）{RESET}")
    print()

    try:
        mode_str = input(f"  {BOLD}>{RESET} ").strip()
        work_mode = "auto" if mode_str == "2" else "manual"
    except (KeyboardInterrupt, EOFError):
        work_mode = "manual"

    if work_mode == "auto":
        _ok(f"自动抢单模式  {DIM}— 配置完成后将打印启动命令{RESET}")
    else:
        _ok(f"手动接单模式  {DIM}— 使用 qgep 命令逐步操作{RESET}")
    print()

    # ── Step 5: Quick Commands (manual only) ────────────────────────────────
    if work_mode == "manual":
        print(f"{CYAN}{BOLD}[5/6] Quick Commands{RESET}\n")
        w = 50
        def row(left, right):
            print(f"  {DIM}│{RESET}  {CYAN}{left:<20}{RESET}  {DIM}{right:<{w-24}}{RESET}{DIM}│{RESET}")
        print(f"  {DIM}┌{'─' * w}┐{RESET}")
        row("qgep list-bounties", "查看任务列表")
        row("qgep claim <id>",    "认领任务")
        row("qgep nodes",         "节点监控")
        row("qgep status",        "排行榜 & Hub 指标")
        row("qgep help",          "所有命令速查")
        print(f"  {DIM}└{'─' * w}┘{RESET}")
        print()

    # ── Step 6: Ready / Launch ───────────────────────────────────────────────
    print(f"{CYAN}{BOLD}[6/6] {'Launching Agent!' if work_mode == 'auto' else 'Ready!'}{RESET}\n")

    cfg2 = load_config()
    hub_addr  = cfg2.get("hub", client.hub)
    agent_id2 = cfg2.get("agent_id", client.agent_id)
    agent_script = Path(__file__).parent / "agent_template.py"

    if work_mode == "auto":
        _ok(f"{GREEN}{BOLD}启动自动接单模式...{RESET}")
        _info(f"Hub: {CYAN}{hub_addr}{RESET}  Agent: {CYAN}{agent_id2}{RESET}")
        print(f"\n  {DIM}按 Ctrl+C 停止 agent{RESET}\n")
        print(f"  {DIM}{'━' * 62}{RESET}\n")
        import subprocess, sys as _sys
        subprocess.run([
            _sys.executable, str(agent_script),
            "--hub", hub_addr,
            "--agent-id", agent_id2,
            "--loop",
        ])
    else:
        _ok(f"{GREEN}{BOLD}Agent is configured and ready.{RESET}")
        print()
        _info(f"运行 {CYAN}qgep list-bounties{RESET} 查看当前任务")
        _info(f"运行 {CYAN}qgep help{RESET} 查看所有命令")
        print()
        print(f"  {DIM}{'━' * 62}{RESET}\n")


def cmd_help(args: argparse.Namespace, client: QGEPClient) -> None:
    """Show categorized command reference."""
    _print_banner()

    def section(title: str) -> None:
        print(f"  {BOLD}{title}{RESET}")
        print(f"  {DIM}{'─' * 45}{RESET}")

    def cmd_row(cmd: str, desc: str) -> None:
        print(f"  {CYAN}{cmd:<28}{RESET}{DIM}{desc}{RESET}")

    section("Getting Started")
    cmd_row("qgep setup",           "交互式配置引导（可重复运行）")
    cmd_row("qgep hello",           "注册节点，获取 500 积分")
    cmd_row("qgep config",          "查看 / 修改 Hub 和 agent_id")
    print()

    section("Task Management")
    cmd_row("qgep list-bounties",   "查看任务列表")
    cmd_row("qgep claim <id>",      "认领任务")
    cmd_row("qgep submit-gene ...", "提交策略基因")
    cmd_row("qgep submit-result ...", "提交任务结果，积分到账")
    print()

    section("Monitoring")
    cmd_row("qgep nodes",           "节点监控（alive / dormant）")
    cmd_row("qgep status",          "排行榜 & Hub 指标")
    cmd_row("qgep heartbeat",       "发送心跳保持在线")
    print()

    section("Gene Library")
    cmd_row("qgep genes",           "浏览基因库")
    cmd_row("qgep genes --search x","按名称搜索基因")
    print()

    print(f"  {DIM}Use `qgep <command> --help` for detailed usage.{RESET}\n")


# ─── Entry point ──────────────────────────────────────────────────────────────

def _print_quantmap_banner() -> None:
    """Full QuantMap ASCII art banner (same as install.sh)."""
    print(f"\n{CYAN}{BOLD}", end="")
    print("  ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗████████╗███╗   ███╗ █████╗ ██████╗ ")
    print(" ██╔═══██╗██║   ██║██╔══██╗████╗  ██║╚══██╔══╝████╗ ████║██╔══██╗██╔══██╗")
    print(" ██║   ██║██║   ██║███████║██╔██╗ ██║   ██║   ██╔████╔██║███████║██████╔╝ ")
    print(" ██║▄▄ ██║██║   ██║██╔══██║██║╚██╗██║   ██║   ██║╚██╔╝██║██╔══██║██╔═══╝  ")
    print(" ╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║   ██║   ██║ ╚═╝ ██║██║  ██║██║      ")
    print(f"  ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝      {RESET}")
    print(f"\n  {DIM}Quantitative Strategy Evolution Network  ·  QGEP-A2A v1.0{RESET}")
    print(f"\n  {DIM}{'━' * 62}{RESET}")


def _test_llm_key(provider: str, api_key: str, model: str, base_url: str) -> Tuple[bool, str]:
    """Test LLM API key validity. Returns (ok, message). Uses only urllib."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    try:
        if provider == "ollama":
            url = (base_url or "http://localhost:11434") + "/api/tags"
            req = urllib.request.Request(url, method="GET")
            with opener.open(req, timeout=10):
                return True, "Ollama reachable"

        elif provider in ("openai", "deepseek"):
            if provider == "deepseek":
                base = (base_url or "https://api.deepseek.com").rstrip("/")
                endpoint = base + "/chat/completions"
            else:
                base = (base_url or "https://api.openai.com").rstrip("/")
                endpoint = base + "/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5,
            }).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            with opener.open(req, timeout=10):
                return True, "API key valid"

        elif provider == "anthropic":
            payload = json.dumps({
                "model": model,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "hi"}],
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with opener.open(req, timeout=10):
                return True, "API key valid"

        return True, "skipped"

    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, f"Invalid API key (HTTP {exc.code})"
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)[:60]


def _print_banner() -> None:
    print(f"\n{CYAN}{BOLD}", end="")
    print("  ██████╗  ██████╗ ███████╗██████╗ ")
    print(" ██╔═══██╗██╔════╝ ██╔════╝██╔══██╗")
    print(" ██║   ██║██║  ███╗█████╗  ██████╔╝")
    print(" ██║▄▄ ██║██║   ██║██╔══╝  ██╔═══╝ ")
    print(" ╚██████╔╝╚██████╔╝███████╗██║      ")
    print(f"  ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝      {RESET}")
    print(f"  {DIM}Quantitative Gene Expression Programming  ·  v1.0{RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="QGEP Client — 量化基因进化协议客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
  {BOLD}Examples:{RESET}
    qgep hello                         # 注册节点，获取 500 积分
    qgep list-bounties                 # 查看待接任务
    qgep claim bounty_xxx              # 认领任务
    qgep submit-gene bounty_xxx --name macd_v1 --formula "MACD(close,12,26,9)"
    qgep submit-result bounty_xxx --gene-id <gene_id>
    qgep nodes                         # 节点监控
    qgep status                        # 排行榜
        """,
    )
    parser.add_argument("--hub",      help="Override Hub URL (e.g. http://192.168.1.100:8889)")
    parser.add_argument("--agent-id", help="Override agent ID")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # config
    p_cfg = sub.add_parser("config", help="Set Hub URL and agent ID")
    p_cfg.add_argument("--hub",      help="Hub base URL")
    p_cfg.add_argument("--agent-id", help="Your agent ID")

    # hello
    sub.add_parser("hello",     help="Register node with Hub (A2A handshake, get 500 credits)")
    sub.add_parser("heartbeat", help="Send keep-alive heartbeat to Hub")
    sub.add_parser("nodes",     help="Monitor all registered nodes and their status")

    # list-bounties
    p_list = sub.add_parser("list-bounties", help="List bounty tasks")
    p_list.add_argument("--status",    default="pending", help="Filter by status (pending/claimed/completed)")
    p_list.add_argument("--task-type", help="Filter by task type")
    p_list.add_argument("--limit",     type=int, default=20)

    # claim
    p_claim = sub.add_parser("claim", help="Claim a bounty task")
    p_claim.add_argument("task_id", help="Task ID to claim")

    # submit-gene
    p_sg = sub.add_parser("submit-gene", help="Submit a strategy gene factor")
    p_sg.add_argument("task_id",      nargs="?",       help="Associated task ID (optional)")
    p_sg.add_argument("--name",       required=True,   help="Gene name")
    p_sg.add_argument("--formula",    required=True,   help="Gene formula/expression")
    p_sg.add_argument("--params",                      help='Parameters as JSON, e.g. \'{"period": 14}\'')
    p_sg.add_argument("--description",                 help="Gene description")

    # submit-result
    p_sr = sub.add_parser("submit-result", help="Submit task result")
    p_sr.add_argument("task_id",      help="Task ID to submit result for")
    p_sr.add_argument("--gene-id",    help="Associated gene ID")
    p_sr.add_argument("--result-data", help='Extra result data as JSON string')

    # status
    sub.add_parser("status", help="Show hub metrics and agent leaderboard")

    # genes
    p_genes = sub.add_parser("genes", help="Browse the gene library")
    p_genes.add_argument("--status", help="Filter: validated/pending/rejected")
    p_genes.add_argument("--search", help="Search by name")
    p_genes.add_argument("--limit",  type=int, default=20)

    # setup / help
    sub.add_parser("setup", help="Interactive setup wizard (run after install)")
    sub.add_parser("help",  help="Show all commands")

    args = parser.parse_args()

    # config doesn't need a client
    if args.cmd == "config":
        cmd_config(args)
        return

    client = QGEPClient(
        hub=getattr(args, "hub", None),
        agent_id=getattr(args, "agent_id", None),
    )

    dispatch = {
        "hello":         cmd_hello,
        "heartbeat":     cmd_heartbeat,
        "nodes":         cmd_nodes,
        "list-bounties": cmd_list_bounties,
        "claim":         cmd_claim,
        "submit-gene":   cmd_submit_gene,
        "submit-result": cmd_submit_result,
        "status":        cmd_status,
        "genes":         cmd_genes,
        "setup":         cmd_setup,
        "help":          cmd_help,
    }

    try:
        dispatch[args.cmd](args, client)
    except RuntimeError as exc:
        print()
        _err(str(exc))
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
