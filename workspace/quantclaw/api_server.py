#!/usr/bin/env python3
"""
Quant EvoMap unified API gateway.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from math import log
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from ecosystem_api import get_ecosystem_data
from evolution_ecosystem import BountyTask, Capsule, Gene, QuantClawEvolutionHub, TaskStatus
from step2_strategy_marketplace import (
    Order,
    OrderType,
    StrategyListing,
    StrategyMarketplace,
)


DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"
MARKET_DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/strategy_marketplace.db"
PID_PATH = Path("/Users/oneday/.openclaw/workspace/quantclaw/evolver.pid")
STATE_PATH = Path("/Users/oneday/.openclaw/workspace/quantclaw/evolver_state.json")


app = FastAPI(title="Quant EvoMap API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

hub = QuantClawEvolutionHub(DB_PATH)
market = StrategyMarketplace(db_path=MARKET_DB_PATH)

# ── 一键安装端点 ───────────────────────────────────────────────────────────────
_SKILL_DIR = Path(__file__).parent.parent / "skills" / "qgep-client"


@app.get("/install.sh", response_class=PlainTextResponse)
def get_install_script(hub_url: str = "", agent_id: str = ""):
    """返回动态生成的一键安装脚本，自动注入 Hub 地址。"""
    script_path = _SKILL_DIR / "install.sh"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="install.sh not found")
    content = script_path.read_text()
    # 动态替换默认 Hub 地址（如果调用方没传就用请求来源）
    if hub_url:
        content = content.replace('HUB="http://127.0.0.1:8889"', f'HUB="{hub_url}"')
    if agent_id:
        content = content.replace("AGENT_ID=\"\"", f'AGENT_ID="{agent_id}"')
    return content


@app.get("/install/qgep_client.py", response_class=PlainTextResponse)
def get_client_script():
    path = _SKILL_DIR / "scripts" / "qgep_client.py"
    if not path.exists():
        raise HTTPException(status_code=404, detail="qgep_client.py not found")
    return path.read_text()


@app.get("/install/agent_template.py", response_class=PlainTextResponse)
def get_agent_template():
    path = _SKILL_DIR / "scripts" / "agent_template.py"
    if not path.exists():
        raise HTTPException(status_code=404, detail="agent_template.py not found")
    return path.read_text()


def _ensure_runtime_tables() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gene_id TEXT,
            agent_id TEXT,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_reputation (
            agent_id TEXT PRIMARY KEY,
            score REAL,
            submissions INTEGER,
            accepted INTEGER,
            validations INTEGER,
            accuracy REAL
        )
        """
    )
    # ── A2A 节点注册表 ──────────────────────────────────────────────────────────
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS a2a_nodes (
            node_id TEXT PRIMARY KEY,
            agent_id TEXT,
            claim_code TEXT,
            credit_balance INTEGER DEFAULT 500,
            registered_at TEXT,
            last_heartbeat TEXT,
            survival_status TEXT DEFAULT 'alive'
        )
        """
    )
    # ── Agent 订阅套餐表 ─────────────────────────────────────────────────────────
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_plans (
            agent_id TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            plan_expires_at TEXT,
            monthly_bounties_used INTEGER DEFAULT 0,
            monthly_genes_used INTEGER DEFAULT 0,
            month_reset_at TEXT,
            updated_at TEXT
        )
        """
    )
    # ── 积分流水表 ───────────────────────────────────────────────────────────────
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            event_type TEXT,
            amount INTEGER,
            ref_id TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


_ensure_runtime_tables()


# ── 套餐配置 ──────────────────────────────────────────────────────────────────

PLANS: Dict[str, Dict[str, Any]] = {
    "free":  {"nodes": 1,  "bounties": 3,  "genes": 5,  "timeout_h": 2,  "rate": 30,  "initial_credits": 500},
    "pro":   {"nodes": 5,  "bounties": 20, "genes": 50, "timeout_h": 6,  "rate": 100, "initial_credits": 2000},
    "ultra": {"nodes": -1, "bounties": -1, "genes": -1, "timeout_h": 24, "rate": 300, "initial_credits": 5000},
}
PLAN_PRICE = {"pro": 299, "ultra": 999}  # credits/月


def _get_agent_plan(agent_id: str) -> Dict[str, Any]:
    """获取 agent 的套餐记录，若不存在则自动创建 free。"""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT plan, plan_expires_at, monthly_bounties_used, monthly_genes_used, month_reset_at FROM agent_plans WHERE agent_id = ?",
        (agent_id,),
    ).fetchone()
    now = datetime.utcnow()

    if not row:
        month_reset = datetime(now.year, now.month, 1).isoformat()
        conn.execute(
            "INSERT INTO agent_plans (agent_id, plan, monthly_bounties_used, monthly_genes_used, month_reset_at, updated_at) VALUES (?, 'free', 0, 0, ?, ?)",
            (agent_id, month_reset, now.isoformat()),
        )
        conn.commit()
        conn.close()
        return {"plan": "free", "monthly_bounties_used": 0, "monthly_genes_used": 0}

    plan, expires_at, bounties_used, genes_used, month_reset_at = row

    # 检查套餐是否到期 → 降回 free
    if plan != "free" and expires_at and datetime.fromisoformat(expires_at) < now:
        conn.execute("UPDATE agent_plans SET plan = 'free', plan_expires_at = NULL WHERE agent_id = ?", (agent_id,))
        conn.commit()
        plan = "free"

    # 检查是否需要重置月度用量
    if month_reset_at:
        reset_dt = datetime.fromisoformat(month_reset_at)
        next_month = datetime(reset_dt.year + (reset_dt.month // 12), (reset_dt.month % 12) + 1, 1)
        if now >= next_month:
            new_reset = datetime(now.year, now.month, 1).isoformat()
            conn.execute(
                "UPDATE agent_plans SET monthly_bounties_used = 0, monthly_genes_used = 0, month_reset_at = ? WHERE agent_id = ?",
                (new_reset, agent_id),
            )
            conn.commit()
            bounties_used, genes_used = 0, 0

    conn.close()
    return {"plan": plan, "monthly_bounties_used": bounties_used, "monthly_genes_used": genes_used}


def _check_quota(agent_id: str, quota_type: str) -> None:
    """检查配额，超限时抛出 HTTPException 429。quota_type: 'bounties' | 'genes' | 'nodes'"""
    rec = _get_agent_plan(agent_id)
    plan = rec["plan"]
    limit = PLANS[plan][quota_type]
    if limit == -1:
        return  # unlimited
    used_key = f"monthly_{quota_type}_used"
    used = rec.get(used_key, 0)
    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "plan": plan,
                "quota_type": quota_type,
                "used": used,
                "limit": limit,
                "message": f"已达 {plan} 套餐每月上限 ({limit})。升级套餐：POST /api/v1/plan/upgrade",
            },
        )


def _increment_quota(agent_id: str, quota_type: str) -> None:
    """配额使用量 +1。quota_type: 'bounties' | 'genes'"""
    col = f"monthly_{quota_type}_used"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"UPDATE agent_plans SET {col} = {col} + 1, updated_at = ? WHERE agent_id = ?",
                 (datetime.utcnow().isoformat(), agent_id))
    conn.commit()
    conn.close()


# ── A2A 协议端点（对齐 EvoMap GEP-A2A）────────────────────────────────────────

def _get_node(node_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT node_id, agent_id, claim_code, credit_balance, registered_at, last_heartbeat, survival_status FROM a2a_nodes WHERE node_id = ?",
        (node_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {"node_id": row[0], "agent_id": row[1], "claim_code": row[2],
            "credit_balance": row[3], "registered_at": row[4],
            "last_heartbeat": row[5], "survival_status": row[6]}


@app.post("/a2a/hello")
def a2a_hello(payload: Dict[str, Any]) -> Dict[str, Any]:
    """节点注册握手。对齐 EvoMap POST /a2a/hello。"""
    sender_id = payload.get("sender_id", "")
    if not sender_id or not sender_id.startswith("node_"):
        raise HTTPException(status_code=400, detail="sender_id must start with 'node_'")

    hub_node_id = "node_quantclaw_hub"
    if sender_id == hub_node_id:
        raise HTTPException(status_code=403, detail="hub_node_id_reserved")

    # 已注册则直接返回
    existing = _get_node(sender_id)
    if existing:
        return {
            "status": "acknowledged",
            "your_node_id": sender_id,
            "hub_node_id": hub_node_id,
            "claim_code": existing["claim_code"],
            "credit_balance": existing["credit_balance"],
            "survival_status": existing["survival_status"],
        }

    # 新注册
    claim_code = "QGEP-" + secrets.token_hex(4).upper()
    now = datetime.utcnow().isoformat()
    agent_id_val = payload.get("payload", {}).get("agent_id", sender_id)
    # 初始余额 500 + 注册奖励 100 + 首连奖励 50 = 650
    initial_balance = 650
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO a2a_nodes (node_id, agent_id, claim_code, credit_balance, registered_at, last_heartbeat, survival_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sender_id, agent_id_val, claim_code, initial_balance, now, now, "alive"),
    )
    conn.commit()
    conn.close()
    # 记录积分流水（初始 500 + 注册奖励 + 首连奖励）
    _record_credit_event(sender_id, "initial_credits", 500, sender_id)
    _record_credit_event(sender_id, "register_node", 100, sender_id)
    _record_credit_event(sender_id, "first_connect", 50, sender_id)
    _audit("a2a_hello", {"sender_id": sender_id, "credit_awarded": 650}, agent_id=sender_id)
    return {
        "status": "acknowledged",
        "your_node_id": sender_id,
        "hub_node_id": hub_node_id,
        "claim_code": claim_code,
        "credit_balance": initial_balance,
        "credit_events": [
            {"event": "initial_credits", "amount": 500},
            {"event": "register_node", "amount": 100},
            {"event": "first_connect", "amount": 50},
        ],
        "survival_status": "alive",
    }


@app.post("/a2a/heartbeat")
def a2a_heartbeat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """节点保活心跳。每 15 分钟一次，45 分钟无心跳标记离线。"""
    sender_id = payload.get("sender_id", "")
    if not sender_id:
        raise HTTPException(status_code=400, detail="sender_id required")

    node = _get_node(sender_id)
    now = datetime.utcnow().isoformat()
    if node:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE a2a_nodes SET last_heartbeat = ?, survival_status = 'alive' WHERE node_id = ?",
            (now, sender_id),
        )
        conn.commit()
        conn.close()
    else:
        # 未注册节点，自动注册
        claim_code = "QGEP-" + secrets.token_hex(4).upper()
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO a2a_nodes (node_id, agent_id, claim_code, credit_balance, registered_at, last_heartbeat, survival_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sender_id, sender_id, claim_code, 500, now, now, "alive"),
        )
        conn.commit()
        conn.close()

    return {"status": "ok", "your_node_id": sender_id, "timestamp": now}


@app.get("/a2a/nodes")
def a2a_nodes() -> Dict[str, Any]:
    """列出所有注册节点及状态。"""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT node_id, agent_id, credit_balance, last_heartbeat, survival_status FROM a2a_nodes ORDER BY last_heartbeat DESC"
    ).fetchall()
    conn.close()
    return {
        "nodes": [
            {"node_id": r[0], "agent_id": r[1], "credit_balance": r[2],
             "last_heartbeat": r[3], "survival_status": r[4]}
            for r in rows
        ]
    }


# ── 后台任务：超时认领自动释放 ─────────────────────────────────────────────────

def _bounty_timeout_loop() -> None:
    """每 5 分钟检查一次，把超时未提交的 claimed 任务释放回 pending。"""
    TIMEOUT_HOURS = 2
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cutoff = (datetime.utcnow() - timedelta(hours=TIMEOUT_HOURS)).isoformat()
            rows = conn.execute(
                "SELECT task_id, claimed_by FROM bounties WHERE status = 'claimed' AND claimed_at < ?",
                (cutoff,),
            ).fetchall()
            for task_id, claimed_by in rows:
                conn.execute(
                    "UPDATE bounties SET status = 'pending', claimed_by = NULL, claimed_at = NULL WHERE task_id = ?",
                    (task_id,),
                )
            if rows:
                conn.commit()
            conn.close()
        except Exception:
            pass
        time.sleep(300)  # 5 分钟


_timeout_thread = threading.Thread(target=_bounty_timeout_loop, daemon=True)
_timeout_thread.start()


# ── A2A 节点状态标记（心跳超时 → dormant）────────────────────────────────────

def _node_status_loop() -> None:
    """每 10 分钟检查节点心跳，45 分钟无心跳 → dormant。"""
    while True:
        try:
            cutoff = (datetime.utcnow() - timedelta(minutes=45)).isoformat()
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE a2a_nodes SET survival_status = 'dormant' WHERE survival_status = 'alive' AND last_heartbeat < ?",
                (cutoff,),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        time.sleep(600)


_node_status_thread = threading.Thread(target=_node_status_loop, daemon=True)
_node_status_thread.start()


def _record_credit_event(agent_id: str, event_type: str, amount: int, ref_id: str = "") -> None:
    """记录积分流水事件到 credit_events 表。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO credit_events (agent_id, event_type, amount, ref_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (agent_id, event_type, amount, ref_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def _award_credits(agent_id: str, amount: int, reason: str, ref_id: str = "") -> int:
    """向 agent_id 对应的节点奖励积分，返回新余额。
    兼容两种情况：agent_id 字段 或 node_id 直接匹配。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE a2a_nodes SET credit_balance = credit_balance + ? WHERE agent_id = ?",
        (amount, agent_id),
    )
    conn.execute(
        "UPDATE a2a_nodes SET credit_balance = credit_balance + ? WHERE node_id = ? AND agent_id != ?",
        (amount, agent_id, agent_id),
    )
    row = conn.execute(
        "SELECT credit_balance FROM a2a_nodes WHERE agent_id = ? OR node_id = ? LIMIT 1",
        (agent_id, agent_id),
    ).fetchone()
    new_balance = row[0] if row else 0
    conn.commit()
    conn.close()
    _record_credit_event(agent_id, reason, amount, ref_id)
    return new_balance


def _audit(action: str, details: Dict[str, Any], agent_id: str = "api_gateway", gene_id: Optional[str] = None) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO audit_trail (gene_id, agent_id, action, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (gene_id, agent_id, action, json.dumps(details, ensure_ascii=True), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def _gene_with_validation(gene: Gene) -> Dict[str, Any]:
    payload = gene.to_gep()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sharpe_ratio, max_drawdown, win_rate, passed, symbol, start_date, end_date
        FROM backtest_results
        WHERE gene_id = ?
        ORDER BY timestamp DESC
        LIMIT 3
        """,
        (gene.gene_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    if rows:
        symbols = [row[4] for row in rows if row[4]]
        payload["validation"] = {
            "status": "validated" if any(bool(row[3]) for row in rows) else "rejected",
            "sharpe_ratio": rows[0][0],
            "max_drawdown": rows[0][1],
            "win_rate": rows[0][2],
            "test_symbols": symbols,
            "test_period": f"{rows[0][5]}:{rows[0][6]}",
        }
    return payload


def _load_genes(limit: int = 100, offset: int = 0) -> List[Gene]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT gene_id FROM genes
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    genes: List[Gene] = []
    for gid in ids:
        gene = hub.get_gene(gid)
        if gene:
            genes.append(gene)
    return genes


@app.get("/api/v1/genes")
def list_genes(limit: int = Query(default=50, ge=1, le=500), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    genes = _load_genes(limit=limit, offset=offset)
    return {
        "items": [_gene_with_validation(gene) for gene in genes],
        "count": len(genes),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/genes/{gene_id}")
def get_gene(gene_id: str) -> Dict[str, Any]:
    gene = hub.get_gene(gene_id)
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")
    return _gene_with_validation(gene)


@app.post("/api/v1/genes")
def submit_gene(payload: Dict[str, Any]) -> Dict[str, Any]:
    author = payload.get("author", payload.get("agent_id", "api_gateway"))
    _check_quota(author, "genes")
    if "lineage" in payload and "meta" in payload:
        gene = Gene.from_gep(payload)
    else:
        gene = Gene(
            gene_id=payload.get("gene_id", ""),
            name=payload.get("name", "UnnamedGene"),
            description=payload.get("description", ""),
            formula=payload.get("formula", ""),
            parameters=payload.get("parameters", {}),
            source=payload.get("source", "manual"),
            author=author,
            created_at=datetime.now(),
            parent_gene_id=payload.get("parent_gene_id"),
            generation=payload.get("generation", 0),
        )
    if not gene.gene_id:
        gene.gene_id = gene.compute_id()
    hub.publish_gene(gene)
    _increment_quota(author, "genes")
    # 基因复用：若有父基因，给原作者 +5
    if gene.parent_gene_id:
        parent = hub.get_gene(gene.parent_gene_id)
        if parent and parent.author and parent.author != author:
            _award_credits(parent.author, 5, "gene_reused", gene.gene_id)
    _audit("submit_gene", {"name": gene.name, "source": gene.source, "parent": gene.parent_gene_id}, gene_id=gene.gene_id)
    return {"ok": True, "gene_id": gene.gene_id}


@app.get("/api/v1/capsules")
def list_capsules(limit: int = Query(default=50, ge=1, le=500)) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM capsules ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    items = []
    for row in rows:
        capsule = Capsule(
            capsule_id=row[0],
            gene_id=row[1],
            code=row[2],
            language=row[3],
            dependencies=json.loads(row[4]) if row[4] else [],
            sharpe_ratio=row[5],
            max_drawdown=row[6],
            win_rate=row[7],
            tested=bool(row[8]),
            validated=bool(row[9]),
            author=row[10],
            created_at=datetime.fromisoformat(row[11]),
        )
        items.append(capsule.to_gep())
    return {"items": items, "count": len(items)}


@app.post("/api/v1/capsules")
def submit_capsule(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "validation" in payload and "meta" in payload:
        capsule = Capsule.from_gep(payload)
    else:
        capsule = Capsule(
            capsule_id=payload.get("capsule_id", ""),
            gene_id=payload.get("gene_id", ""),
            code=payload.get("code", ""),
            language=payload.get("language", "python"),
            dependencies=payload.get("dependencies", []),
            sharpe_ratio=payload.get("sharpe_ratio", 0.0),
            max_drawdown=payload.get("max_drawdown", 0.0),
            win_rate=payload.get("win_rate", 0.0),
            tested=payload.get("tested", False),
            validated=payload.get("validated", False),
            author=payload.get("author", "api_gateway"),
            created_at=datetime.now(),
        )
    if not capsule.capsule_id:
        capsule.capsule_id = capsule.compute_id()
    hub.publish_capsule(capsule)
    _audit("submit_capsule", {"gene_id": capsule.gene_id}, gene_id=capsule.gene_id)
    return {"ok": True, "capsule_id": capsule.capsule_id}


@app.get("/api/v1/events")
def list_events(limit: int = Query(default=100, ge=1, le=1000)) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    items = []
    for row in rows:
        items.append(
            {
                "event_id": row[0],
                "gene_id": row[1],
                "capsule_id": row[2],
                "event_type": row[3],
                "trigger": row[4],
                "test_data": json.loads(row[5]) if row[5] else {},
                "gdi_score": row[6],
                "meta": {
                    "author": row[7],
                    "timestamp": row[8],
                },
            }
        )
    return {"items": items, "count": len(items)}


@app.get("/api/v1/bounties")
def list_bounties(status: Optional[str] = None) -> Dict[str, Any]:
    if status:
        bounties = hub.list_bounties(status=TaskStatus(status))
    else:
        bounties = hub.list_bounties()
    return {
        "items": [
            {
                "task_id": b.task_id,
                "title": b.title,
                "description": b.description,
                "task_type": b.task_type,
                "status": b.status.value,
                "reward_credits": b.reward_credits,
                "requirements": b.requirements,
                "claimed_by": b.claimed_by,
                "result_bundle_id": b.result_bundle_id,
                "created_at": b.created_at.isoformat(),
                "deadline": b.deadline.isoformat() if b.deadline else None,
            }
            for b in bounties
        ]
    }


@app.post("/api/v1/bounties")
def create_bounty(payload: Dict[str, Any]) -> Dict[str, Any]:
    bounty = BountyTask(
        task_id="",
        title=payload.get("title", "Untitled bounty"),
        description=payload.get("description", ""),
        task_type=payload.get("task_type", "discover_factor"),
        reward_credits=payload.get("reward_credits", 100),
        difficulty=payload.get("difficulty", 3),
        requirements=payload.get("requirements", {}),
        deadline=datetime.fromisoformat(payload["deadline"]) if payload.get("deadline") else None,
    )
    task_id = hub.create_bounty(bounty)
    _audit("create_bounty", {"task_id": task_id})
    return {"ok": True, "task_id": task_id}


@app.post("/api/v1/bounties/{task_id}/claim")
def claim_bounty(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = payload.get("agent_id", "unknown_agent")
    _check_quota(agent_id, "bounties")
    success = hub.claim_bounty(task_id, agent_id)
    if not success:
        raise HTTPException(status_code=409, detail="Cannot claim bounty")
    _increment_quota(agent_id, "bounties")
    _audit("claim_bounty", {"task_id": task_id}, agent_id=agent_id)
    return {"ok": True}


@app.post("/api/v1/bounties/{task_id}/submit")
def submit_bounty(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = payload.get("agent_id", "unknown_agent")
    bundle_id = payload.get("bundle_id", "")
    if not bundle_id:
        raise HTTPException(status_code=400, detail="bundle_id is required")
    # 查询赏金奖励金额（完成前先读）
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT reward_credits FROM bounties WHERE task_id = ?", (task_id,)).fetchone()
    conn.close()
    reward = row[0] if row else 0
    success = hub.complete_bounty(task_id, agent_id, bundle_id)
    if not success:
        raise HTTPException(status_code=409, detail="Cannot complete bounty")
    # 奖励积分打入节点余额
    new_balance = _award_credits(agent_id, reward, "bounty_reward", task_id)
    _audit("submit_bounty", {"task_id": task_id, "bundle_id": bundle_id, "reward_credits": reward}, agent_id=agent_id)
    return {"ok": True, "reward_credits": reward, "new_balance": new_balance}


@app.get("/api/v1/market/listings")
def market_listings(
    strategy_type: Optional[str] = None,
    min_sharpe: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "score",
) -> Dict[str, Any]:
    items = market.search_strategies(strategy_type=strategy_type, min_sharpe=min_sharpe, max_price=max_price, sort_by=sort_by)
    return {"items": [item.to_dict() for item in items], "count": len(items)}


@app.post("/api/v1/market/listings")
async def create_listing(payload: Dict[str, Any]) -> Dict[str, Any]:
    listing = StrategyListing(
        listing_id="",
        seller_id=payload.get("seller_id", "unknown_seller"),
        bundle_id=payload.get("bundle_id", ""),
        gene_id=payload.get("gene_id", ""),
        capsule_id=payload.get("capsule_id", ""),
        title=payload.get("title", "Untitled Strategy"),
        description=payload.get("description", ""),
        strategy_type=payload.get("strategy_type", "unknown"),
        sharpe_ratio=float(payload.get("sharpe_ratio", 0.0)),
        max_drawdown=float(payload.get("max_drawdown", 0.0)),
        annual_return=float(payload.get("annual_return", 0.0)),
        win_rate=float(payload.get("win_rate", 0.0)),
        backtest_period=payload.get("backtest_period", "unknown"),
        validation_count=int(payload.get("validation_count", 2)),
        validator_scores=payload.get("validator_scores", [80.0, 78.0]),
        price=float(payload.get("price", 100.0)),
        price_model=payload.get("price_model", "fixed"),
        license_type=payload.get("license_type", "one_time"),
        royalty_rate=float(payload.get("royalty_rate", 0.0)),
    )
    listing_id = market.list_strategy(listing)
    # 上架奖励 +100
    new_balance = _award_credits(listing.seller_id, 100, "listing_created", listing_id)
    _audit("create_listing", {"listing_id": listing_id, "bundle_id": listing.bundle_id, "credit_awarded": 100}, agent_id=listing.seller_id)
    return {"ok": True, "listing_id": listing_id, "credit_awarded": 100, "new_balance": new_balance}


@app.post("/api/v1/market/orders")
async def create_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    order_type = payload.get("order_type", "buy")
    order = Order(
        order_id="",
        order_type=OrderType(order_type),
        trader_id=payload.get("trader_id", "unknown_buyer"),
        listing_id=payload.get("listing_id"),
        strategy_type=payload.get("strategy_type"),
        price=float(payload.get("price", 100.0)),
        price_tolerance=float(payload.get("price_tolerance", 0.1)),
        quantity=int(payload.get("quantity", 1)),
        min_sharpe=payload.get("min_sharpe"),
        max_drawdown=payload.get("max_drawdown"),
        min_validation_count=int(payload.get("min_validation_count", 1)),
    )
    order_id = market.place_order(order)
    _audit("create_order", {"order_id": order_id, "type": order_type}, agent_id=order.trader_id)
    return {"ok": True, "order_id": order_id}


@app.get("/api/v1/ecosystem")
def ecosystem() -> Dict[str, Any]:
    return get_ecosystem_data()


@app.get("/api/v1/stats")
def stats() -> Dict[str, Any]:
    return get_ecosystem_data()["stats"]


@app.get("/api/ecosystem")
def ecosystem_legacy() -> Dict[str, Any]:
    return get_ecosystem_data()


@app.get("/api/stats")
def stats_legacy() -> Dict[str, Any]:
    return get_ecosystem_data()["stats"]


@app.get("/api/v1/evolver/status")
def evolver_status() -> Dict[str, Any]:
    pid = None
    running = False
    if PID_PATH.exists():
        try:
            pid = int(PID_PATH.read_text().strip())
            import os

            os.kill(pid, 0)
            running = True
        except Exception:
            running = False
    state: Dict[str, Any] = {}
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text())
        except json.JSONDecodeError:
            state = {}
    return {"running": running, "pid": pid, "state": state}


@app.get("/api/v1/metrics")
def metrics(avg_backtest_cost: float = 1.0) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM genes")
    total_genes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM genes WHERE parent_gene_id IS NOT NULL")
    reuse_count = cursor.fetchone()[0]
    cursor.execute("SELECT formula FROM genes")
    formulas = [row[0] for row in cursor.fetchall()]
    cursor.execute(
        """
        SELECT agent_id, score, submissions, accepted, validations, accuracy
        FROM agent_reputation
        ORDER BY score DESC
        LIMIT 10
        """
    )
    top_agents = cursor.fetchall()
    conn.close()

    saved_compute = reuse_count * avg_backtest_cost

    entropy = 0.0
    if formulas:
        counter = Counter(formulas)
        total = sum(counter.values())
        for _, count in counter.items():
            p = count / total
            entropy -= p * log(p) if p > 0 else 0.0

    return {
        "totals": {
            "genes": total_genes,
            "events": total_events,
            "reused_genes": reuse_count,
        },
        "negentropy": {
            "saved_compute": saved_compute,
            "shannon_diversity": entropy,
        },
        "trust": {
            "top_agents": [
                {
                    "agent_id": row[0],
                    "score": row[1],
                    "submissions": row[2],
                    "accepted": row[3],
                    "validations": row[4],
                    "accuracy": row[5],
                }
                for row in top_agents
            ]
        },
    }


# ── 验证报告端点（+20 积分）────────────────────────────────────────────────────

@app.post("/api/v1/validations")
def submit_validation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """提交基因验证报告，获得 +20 积分奖励。
    payload: { agent_id, gene_id, sharpe_ratio, max_drawdown, win_rate, symbol, passed }
    """
    agent_id = payload.get("agent_id", "unknown_agent")
    gene_id = payload.get("gene_id", "")
    if not gene_id:
        raise HTTPException(status_code=400, detail="gene_id is required")

    # 写入 backtest_results 表（复用已有表结构）
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO backtest_results (gene_id, sharpe_ratio, max_drawdown, win_rate, passed, symbol, start_date, end_date, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            gene_id,
            float(payload.get("sharpe_ratio", 0.0)),
            float(payload.get("max_drawdown", 0.0)),
            float(payload.get("win_rate", 0.0)),
            1 if payload.get("passed", False) else 0,
            payload.get("symbol", ""),
            payload.get("start_date", ""),
            payload.get("end_date", ""),
            now,
        ),
    )
    conn.commit()
    conn.close()

    # 奖励积分
    new_balance = _award_credits(agent_id, 20, "validation_report", gene_id)
    _audit("submit_validation", {"gene_id": gene_id, "passed": payload.get("passed")}, agent_id=agent_id, gene_id=gene_id)
    return {"ok": True, "credit_awarded": 20, "new_balance": new_balance}


@app.get("/api/v1/credits/{agent_id}")
def get_credit_history(agent_id: str, limit: int = Query(default=50, ge=1, le=200)) -> Dict[str, Any]:
    """查询 agent 的积分余额和流水记录。"""
    # 查余额
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT credit_balance FROM a2a_nodes WHERE agent_id = ? OR node_id = ? LIMIT 1",
        (agent_id, agent_id),
    ).fetchone()
    balance = row[0] if row else 0

    # 查流水
    events = conn.execute(
        "SELECT event_type, amount, ref_id, created_at FROM credit_events WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
        (agent_id, limit),
    ).fetchall()
    conn.close()

    return {
        "agent_id": agent_id,
        "credit_balance": balance,
        "events": [
            {"event_type": e[0], "amount": e[1], "ref_id": e[2], "created_at": e[3]}
            for e in events
        ],
    }


# ── 套餐查询 & 升级端点 ────────────────────────────────────────────────────────

@app.get("/api/v1/plan")
def get_plan(agent_id: str) -> Dict[str, Any]:
    """查询 agent 当前套餐和月度用量。"""
    rec = _get_agent_plan(agent_id)
    plan = rec["plan"]
    limits = PLANS[plan]
    return {
        "agent_id": agent_id,
        "plan": plan,
        "limits": limits,
        "usage": {
            "monthly_bounties_used": rec["monthly_bounties_used"],
            "monthly_genes_used": rec["monthly_genes_used"],
        },
        "upgrade_options": {
            k: {"price_credits_per_month": v, "limits": PLANS[k]}
            for k, v in PLAN_PRICE.items()
            if k != plan
        },
    }


@app.post("/api/v1/plan/upgrade")
def upgrade_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    """升级套餐，扣除积分。payload: {agent_id, target_plan}"""
    agent_id = payload.get("agent_id", "")
    target = payload.get("target_plan", "")
    if not agent_id or target not in ("pro", "ultra"):
        raise HTTPException(status_code=400, detail="agent_id and target_plan (pro/ultra) required")

    price = PLAN_PRICE[target]
    # 检查节点积分余额
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT credit_balance FROM a2a_nodes WHERE agent_id = ? ORDER BY registered_at DESC LIMIT 1",
        (agent_id,),
    ).fetchone()
    if not row or row[0] < price:
        conn.close()
        raise HTTPException(status_code=402, detail=f"积分不足，需要 {price} credits，当前 {row[0] if row else 0}")

    # 扣积分
    conn.execute(
        "UPDATE a2a_nodes SET credit_balance = credit_balance - ? WHERE agent_id = ?",
        (price, agent_id),
    )
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    conn.execute(
        """INSERT INTO agent_plans (agent_id, plan, plan_expires_at, monthly_bounties_used, monthly_genes_used, month_reset_at, updated_at)
           VALUES (?, ?, ?, 0, 0, ?, ?)
           ON CONFLICT(agent_id) DO UPDATE SET plan=excluded.plan, plan_expires_at=excluded.plan_expires_at, updated_at=excluded.updated_at""",
        (agent_id, target, expires_at, datetime(datetime.utcnow().year, datetime.utcnow().month, 1).isoformat(), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    _audit("upgrade_plan", {"target_plan": target, "price": price}, agent_id=agent_id)
    return {"ok": True, "plan": target, "expires_at": expires_at, "credits_deducted": price}


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="QGEP API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (use 0.0.0.0 to allow external access)")
    parser.add_argument("--port", type=int, default=8889, help="Bind port")
    srv_args = parser.parse_args()

    uvicorn.run(app, host=srv_args.host, port=srv_args.port)
