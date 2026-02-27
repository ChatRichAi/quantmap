#!/usr/bin/env python3
"""
QGEP Agent Template — 可直接扩展的赏金任务执行器模板

用法：
  1. 复制本文件，重命名为 my_agent.py
  2. 实现 discover_factor() / optimize_strategy() / implement_paper() 方法
  3. 运行: python3 my_agent.py --hub http://HUB_IP:8889 --agent-id my_agent_01
     or:   python3 my_agent.py --once   # 单次运行
     or:   python3 my_agent.py --loop   # 持续轮询
"""

from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from typing import Any, Dict, Optional

# 导入客户端（同目录）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from qgep_client import QGEPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("qgep-agent")


# ─── 任务处理逻辑（在此实现你的策略）────────────────────────────────────────────

def discover_factor(bounty: Dict[str, Any], client: QGEPClient) -> Optional[str]:
    """
    发现新量化因子。
    返回: gene_id（提交成功），或 None（跳过/失败）
    """
    task_id = bounty.get("task_id") or bounty.get("id")
    log.info(f"Discovering factor for task {task_id}: {bounty.get('title', '')}")

    # ── 在这里实现你的因子发现逻辑 ──
    # 例如：调用本地模型、读取数据、计算因子
    # 示例（占位，请替换为真实逻辑）：
    formula = "RSI(close, 14) - MA(RSI(close, 14), 5)"
    params = {"rsi_period": 14, "ma_period": 5}
    gene_name = f"rsi_deviation_{int(time.time())}"
    # ─────────────────────────────────

    gene_id = client.submit_gene(
        name=gene_name,
        formula=formula,
        parameters=params,
        task_id=task_id,
        description=f"Auto-discovered by {client.agent_id}",
    )
    log.info(f"Submitted gene: {gene_id}")
    return gene_id


def optimize_strategy(bounty: Dict[str, Any], client: QGEPClient) -> Optional[str]:
    """
    优化已有策略参数。
    返回: gene_id 或 None
    """
    task_id = bounty.get("task_id") or bounty.get("id")
    log.info(f"Optimizing strategy for task {task_id}")

    # ── 实现参数优化逻辑 ──
    # 例如：网格搜索、贝叶斯优化、RL
    requirements = bounty.get("requirements") or {}
    base_formula = requirements.get("base_formula", "MACD(close, 12, 26, 9)")
    optimized_params = {"fast": 10, "slow": 22, "signal": 7}  # 示例
    gene_name = f"optimized_{int(time.time())}"
    # ─────────────────────

    gene_id = client.submit_gene(
        name=gene_name,
        formula=base_formula,
        parameters=optimized_params,
        task_id=task_id,
    )
    log.info(f"Submitted optimized gene: {gene_id}")
    return gene_id


def implement_paper(bounty: Dict[str, Any], client: QGEPClient) -> Optional[str]:
    """
    实现学术论文策略。
    返回: gene_id 或 None
    """
    task_id = bounty.get("task_id") or bounty.get("id")
    log.info(f"Implementing paper strategy for task {task_id}")

    # ── 实现论文策略 ──
    requirements = bounty.get("requirements") or {}
    paper_formula = requirements.get("formula", "MOM(close, 20) / STD(close, 20)")
    gene_name = f"paper_impl_{int(time.time())}"
    # ─────────────────

    gene_id = client.submit_gene(
        name=gene_name,
        formula=paper_formula,
        task_id=task_id,
    )
    log.info(f"Submitted paper gene: {gene_id}")
    return gene_id


# ─── 调度器 ───────────────────────────────────────────────────────────────────

HANDLERS = {
    "discover_factor": discover_factor,
    "optimize_strategy": optimize_strategy,
    "implement_paper": implement_paper,
}


def run_once(client: QGEPClient) -> bool:
    """领取并处理一个可用任务。返回是否处理了任务。"""
    bounties = client.list_bounties(status="pending", limit=10)
    if not bounties:
        log.info("No pending bounties.")
        return False

    for bounty in bounties:
        task_id = bounty.get("task_id") or bounty.get("id")
        task_type = bounty.get("task_type", "")
        handler = HANDLERS.get(task_type)
        if not handler:
            log.warning(f"Unknown task_type '{task_type}', skipping {task_id}")
            continue

        # 认领
        try:
            client.claim(task_id)
            log.info(f"Claimed task {task_id} ({task_type})")
        except RuntimeError as exc:
            log.warning(f"Cannot claim {task_id}: {exc}")
            continue

        # 执行
        gene_id = None
        try:
            gene_id = handler(bounty, client)
        except Exception as exc:
            log.error(f"Handler failed for {task_id}: {exc}")

        # 提交结果
        try:
            result = client.submit_result(
                task_id=task_id,
                gene_id=gene_id,
                result_data={"status": "completed" if gene_id else "failed"},
            )
            log.info(f"Submitted result: {result}")
        except RuntimeError as exc:
            log.error(f"Failed to submit result for {task_id}: {exc}")

        return True

    return False


def _heartbeat_loop(client: QGEPClient, interval: int = 900) -> None:
    """后台线程：每 interval 秒发送一次心跳（默认 15 分钟）。"""
    while True:
        time.sleep(interval)
        try:
            client.a2a_heartbeat()
            log.debug("Heartbeat sent.")
        except Exception as exc:
            log.warning(f"Heartbeat failed: {exc}")


def run_loop(client: QGEPClient, interval: int = 60) -> None:
    """持续轮询，每隔 interval 秒检查一次新任务。心跳在后台线程运行。"""
    log.info(f"Starting QGEP agent loop (hub={client.hub}, agent={client.agent_id}, interval={interval}s)")
    # 后台心跳线程（每 15 分钟，不阻塞主循环）
    hb_thread = threading.Thread(target=_heartbeat_loop, args=(client,), daemon=True)
    hb_thread.start()
    while True:
        try:
            handled = run_once(client)
            if not handled:
                log.info(f"Sleeping {interval}s ...")
                time.sleep(interval)
        except KeyboardInterrupt:
            log.info("Agent stopped.")
            break
        except Exception as exc:
            log.error(f"Unexpected error: {exc}")
            time.sleep(interval)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QGEP Agent Template")
    parser.add_argument("--hub", help="Hub URL, e.g. http://192.168.1.1:8889")
    parser.add_argument("--agent-id", default=None, help="Your agent ID")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run once and exit")
    mode.add_argument("--loop", action="store_true", help="Run in loop (default)")
    args = parser.parse_args()

    client = QGEPClient(hub=args.hub, agent_id=args.agent_id)

    if not client.ping():
        log.error(f"Cannot reach Hub at {client.hub}. Check the address and network.")
        return

    log.info(f"Connected to Hub: {client.hub}  agent_id: {client.agent_id}")

    # A2A Hello — 注册节点（首次运行获取 claim_code 和初始积分）
    try:
        hello_resp = client.a2a_hello()
        log.info(
            f"A2A Hello: node_id={hello_resp.get('your_node_id')}  "
            f"claim_code={hello_resp.get('claim_code')}  "
            f"credits={hello_resp.get('credit_balance')}"
        )
    except Exception as exc:
        log.warning(f"A2A Hello failed (non-fatal): {exc}")

    if args.once:
        run_once(client)
    else:
        run_loop(client, interval=args.interval)


if __name__ == "__main__":
    main()
