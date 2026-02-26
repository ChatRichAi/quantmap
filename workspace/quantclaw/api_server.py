#!/usr/bin/env python3
"""
Quant EvoMap unified API gateway.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime
from math import log
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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
    conn.commit()
    conn.close()


_ensure_runtime_tables()


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
            author=payload.get("author", "api_gateway"),
            created_at=datetime.now(),
            parent_gene_id=payload.get("parent_gene_id"),
            generation=payload.get("generation", 0),
        )
    if not gene.gene_id:
        gene.gene_id = gene.compute_id()
    hub.publish_gene(gene)
    _audit("submit_gene", {"name": gene.name, "source": gene.source}, gene_id=gene.gene_id)
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
    success = hub.claim_bounty(task_id, agent_id)
    if not success:
        raise HTTPException(status_code=409, detail="Cannot claim bounty")
    _audit("claim_bounty", {"task_id": task_id}, agent_id=agent_id)
    return {"ok": True}


@app.post("/api/v1/bounties/{task_id}/submit")
def submit_bounty(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = payload.get("agent_id", "unknown_agent")
    bundle_id = payload.get("bundle_id", "")
    if not bundle_id:
        raise HTTPException(status_code=400, detail="bundle_id is required")
    success = hub.complete_bounty(task_id, agent_id, bundle_id)
    if not success:
        raise HTTPException(status_code=409, detail="Cannot complete bounty")
    _audit("submit_bounty", {"task_id": task_id, "bundle_id": bundle_id}, agent_id=agent_id)
    return {"ok": True}


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
    _audit("create_listing", {"listing_id": listing_id, "bundle_id": listing.bundle_id}, agent_id=listing.seller_id)
    return {"ok": True, "listing_id": listing_id}


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


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="QGEP API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (use 0.0.0.0 to allow external access)")
    parser.add_argument("--port", type=int, default=8889, help="Bind port")
    srv_args = parser.parse_args()

    uvicorn.run(app, host=srv_args.host, port=srv_args.port)
