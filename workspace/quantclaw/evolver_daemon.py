#!/usr/bin/env python3
"""
Quant EvoMap Evolver Daemon.

Runs a continuous GEP-like loop:
Scan -> Signal -> Intent -> Mutate -> Validate -> Solidify.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from darwinian_ecosystem_v4 import DarwinianEcosystem
from evolution_ecosystem import EvolutionEvent, QuantClawEvolutionHub
from factor_backtest_validator import FactorValidator
from self_driving_evolution_v3 import SelfDrivingEvolutionSystem


DEFAULT_DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"
DEFAULT_ROOT = Path("/Users/oneday/.openclaw/workspace/quantclaw")
DEFAULT_PID_PATH = DEFAULT_ROOT / "evolver.pid"
DEFAULT_STATE_PATH = DEFAULT_ROOT / "evolver_state.json"
DEFAULT_LOG_PATH = DEFAULT_ROOT / "logs" / "evolver.log"
DEFAULT_AGENT_ID = "evolver_daemon"


@dataclass
class EvolutionSignal:
    signal_type: str
    severity: str
    message: str
    payload: Dict[str, Any]


class EvolverDaemon:
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        state_path: Path = DEFAULT_STATE_PATH,
        log_path: Path = DEFAULT_LOG_PATH,
        min_interval: int = 300,
        max_interval: int = 7200,
    ):
        self.db_path = db_path
        self.state_path = state_path
        self.log_path = log_path
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.agent_id = DEFAULT_AGENT_ID

        self.running = True
        self.hub = QuantClawEvolutionHub(self.db_path)
        self.self_driving = SelfDrivingEvolutionSystem(self.db_path)
        self.darwin = DarwinianEcosystem(self.db_path)
        self.validator = FactorValidator(self.db_path)

        self._ensure_runtime_tables()
        self.state = self._load_state()

    def _ensure_runtime_tables(self) -> None:
        conn = sqlite3.connect(self.db_path)
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
        cursor.execute(
            """
            INSERT OR IGNORE INTO agent_reputation
            (agent_id, score, submissions, accepted, validations, accuracy)
            VALUES (?, 60.0, 0, 0, 0, 0.0)
            """,
            (self.agent_id,),
        )
        conn.commit()
        conn.close()

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except json.JSONDecodeError:
                pass
        return {
            "started_at": datetime.now().isoformat(),
            "cycles": 0,
            "last_interval_seconds": 900,
            "last_cycle": None,
        }

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def _log(self, level: str, message: str, **extra: Any) -> None:
        payload = {
            "ts": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **extra,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    def _audit(self, action: str, details: Dict[str, Any], gene_id: Optional[str] = None) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_trail (gene_id, agent_id, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                gene_id,
                self.agent_id,
                action,
                json.dumps(details, ensure_ascii=True),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def scan(self) -> Dict[str, Any]:
        diagnosis = self.self_driving.self_diagnose()
        now = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM genes")
        pool_size = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT formula) FROM genes")
        unique_formula_count = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(created_at) FROM genes")
        last_gene_ts = cursor.fetchone()[0]
        conn.close()

        diversity = (unique_formula_count / pool_size) if pool_size else 0.0
        hours_since_new_gene = None
        if last_gene_ts:
            try:
                last_dt = datetime.fromisoformat(last_gene_ts)
                hours_since_new_gene = (now - last_dt).total_seconds() / 3600.0
            except ValueError:
                hours_since_new_gene = None

        return {
            "pool_size": pool_size,
            "diversity": diversity,
            "hours_since_new_gene": hours_since_new_gene,
            "diagnosis": {
                "severity": diagnosis.severity,
                "issues": diagnosis.issues,
                "recommendations": diagnosis.recommendations,
            },
        }

    def signalize(self, scan_result: Dict[str, Any]) -> List[EvolutionSignal]:
        signals: List[EvolutionSignal] = []
        for issue in scan_result["diagnosis"]["issues"]:
            signals.append(
                EvolutionSignal(
                    signal_type=issue["type"],
                    severity=issue["severity"],
                    message=issue["message"],
                    payload=issue,
                )
            )
        if scan_result["pool_size"] <= 10:
            signals.append(
                EvolutionSignal(
                    signal_type="small_pool",
                    severity="warning",
                    message="Pool size below healthy threshold",
                    payload={"pool_size": scan_result["pool_size"]},
                )
            )
        if scan_result["hours_since_new_gene"] and scan_result["hours_since_new_gene"] > 6:
            signals.append(
                EvolutionSignal(
                    signal_type="stale_generation",
                    severity="warning",
                    message="No new genes in the last 6 hours",
                    payload={"hours_since_new_gene": scan_result["hours_since_new_gene"]},
                )
            )
        if not signals:
            signals.append(
                EvolutionSignal(
                    signal_type="routine_cycle",
                    severity="info",
                    message="No major issues, run normal evolution cycle",
                    payload={},
                )
            )
        return signals

    def decide_intent(self, signals: List[EvolutionSignal]) -> str:
        signal_types = {s.signal_type for s in signals}
        if "lineage_dominance" in signal_types or "low_diversity" in signal_types:
            return "diversity_repair"
        if "high_backtest_failure" in signal_types:
            return "quality_repair"
        if "small_pool" in signal_types:
            return "pool_expansion"
        if "stale_generation" in signal_types or "evolution_stagnation" in signal_types:
            return "exploration_boost"
        return "routine_evolution"

    def mutate(self, intent: str) -> Dict[str, Any]:
        if intent == "pool_expansion":
            self.self_driving._generate_emergency_seeds()
            report = self.self_driving.evolve_generation_self_driving(population_size=12)
            return {"intent": intent, "mode": "seed_and_evolve", "report": report}
        if intent == "diversity_repair":
            self.self_driving._auto_discover_seeds()
            report = self.self_driving.evolve_generation_self_driving(population_size=14)
            return {"intent": intent, "mode": "discover_and_evolve", "report": report}
        if intent == "quality_repair":
            self.self_driving._fix_indicator_implementations()
            darwin_report = self.darwin.survival_challenge()
            return {"intent": intent, "mode": "darwinian_cull", "report": darwin_report}
        if intent == "exploration_boost":
            self.self_driving.adaptive_params["mutation_rate"] = min(
                0.6, self.self_driving.adaptive_params["mutation_rate"] + 0.1
            )
            report = self.self_driving.evolve_generation_self_driving(population_size=16)
            return {"intent": intent, "mode": "mutation_boost", "report": report}
        report = self.self_driving.evolve_generation_self_driving(population_size=10)
        return {"intent": intent, "mode": "routine", "report": report}

    def validate(self) -> Dict[str, Any]:
        cutoff = (datetime.now() - timedelta(hours=2)).isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM genes WHERE created_at >= ?
            ORDER BY created_at DESC LIMIT 5
            """,
            (cutoff,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"validated": 0, "passed": 0, "pass_rate": 0.0}

        passed = 0
        validated = 0
        for row in rows:
            gene_id = row[0]
            gene = self.hub.get_gene(gene_id)
            if not gene:
                continue
            try:
                results = self.validator.validate_gene(gene, symbols=["AAPL"], start_date="2022-01-01", end_date="2024-12-31")
                validated += 1
                if any(r.passed for r in results):
                    passed += 1
                self._audit("validate_gene", {"passed": any(r.passed for r in results)}, gene_id=gene_id)
            except Exception as exc:
                self._log("error", "Validation error", gene_id=gene_id, error=str(exc))

        pass_rate = passed / validated if validated else 0.0
        self._update_reputation(submissions=validated, accepted=passed, validations=validated, accuracy=pass_rate)
        return {"validated": validated, "passed": passed, "pass_rate": pass_rate}

    def solidify(self, cycle_data: Dict[str, Any], validation_data: Dict[str, Any]) -> Dict[str, Any]:
        event = EvolutionEvent(
            event_id=f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            gene_id="system",
            capsule_id="system",
            event_type="daemon_cycle",
            trigger=cycle_data.get("intent", "unknown"),
            test_data={
                "cycle": cycle_data,
                "validation": validation_data,
            },
            gdi_score=100.0 * validation_data.get("pass_rate", 0.0),
            author=self.agent_id,
            timestamp=datetime.now(),
        )
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.gene_id,
                event.capsule_id,
                event.event_type,
                event.trigger,
                json.dumps(event.test_data, ensure_ascii=True),
                event.gdi_score,
                event.author,
                event.timestamp.isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        self._audit("solidify_cycle", {"event_id": event.event_id, "gdi_score": event.gdi_score})
        return {"event_id": event.event_id, "gdi_score": event.gdi_score}

    def compute_interval(self, scan_result: Dict[str, Any], validation_data: Dict[str, Any]) -> int:
        interval = 900
        if scan_result["diagnosis"]["severity"] == "critical":
            interval = 300
        elif validation_data.get("pass_rate", 0) < 0.3:
            interval = 1800
        elif scan_result.get("pool_size", 0) > 150:
            interval = 1200
        return max(self.min_interval, min(self.max_interval, interval))

    def run_cycle(self) -> Dict[str, Any]:
        scan_result = self.scan()
        signals = self.signalize(scan_result)
        intent = self.decide_intent(signals)
        mutation_data = self.mutate(intent)
        validation_data = self.validate()
        solidified = self.solidify(mutation_data, validation_data)
        interval = self.compute_interval(scan_result, validation_data)

        cycle = {
            "at": datetime.now().isoformat(),
            "scan": scan_result,
            "signals": [asdict(s) for s in signals],
            "intent": intent,
            "mutation": mutation_data,
            "validation": validation_data,
            "solidify": solidified,
            "next_interval_seconds": interval,
        }
        self._audit("run_cycle", {"intent": intent, "pass_rate": validation_data.get("pass_rate", 0.0)})
        return cycle

    def _update_reputation(
        self,
        submissions: int = 0,
        accepted: int = 0,
        validations: int = 0,
        accuracy: float = 0.0,
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT score, submissions, accepted, validations, accuracy
            FROM agent_reputation WHERE agent_id = ?
            """,
            (self.agent_id,),
        )
        row = cursor.fetchone()
        if not row:
            score, old_sub, old_acc, old_val, old_accuracy = 60.0, 0, 0, 0, 0.0
        else:
            score, old_sub, old_acc, old_val, old_accuracy = row

        new_sub = old_sub + submissions
        new_acc = old_acc + accepted
        new_val = old_val + validations
        blend = old_accuracy * 0.7 + accuracy * 0.3
        accept_rate = (new_acc / new_sub) if new_sub else 0.0
        new_score = max(0.0, min(100.0, accept_rate * 60.0 + blend * 40.0))

        cursor.execute(
            """
            INSERT OR REPLACE INTO agent_reputation
            (agent_id, score, submissions, accepted, validations, accuracy)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (self.agent_id, new_score, new_sub, new_acc, new_val, blend),
        )
        conn.commit()
        conn.close()

    def run_forever(self) -> None:
        self._log("info", "Evolver daemon started", db_path=self.db_path)

        def _handle_signal(sig: int, _: Any) -> None:
            self._log("info", "Signal received, shutting down", signal=sig)
            self.running = False

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        while self.running:
            try:
                cycle = self.run_cycle()
                self.state["cycles"] += 1
                self.state["last_cycle"] = cycle
                self.state["last_interval_seconds"] = cycle["next_interval_seconds"]
                self._save_state()
                self._log(
                    "info",
                    "Cycle completed",
                    cycle=self.state["cycles"],
                    intent=cycle["intent"],
                    pass_rate=cycle["validation"]["pass_rate"],
                    next_sleep=cycle["next_interval_seconds"],
                )
                time.sleep(cycle["next_interval_seconds"])
            except Exception as exc:
                self._log("error", "Cycle failed", error=str(exc))
                time.sleep(min(self.max_interval, 1200))

        self._log("info", "Evolver daemon stopped", total_cycles=self.state["cycles"])


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_pid(pid_path: Path) -> Optional[int]:
    if not pid_path.exists():
        return None
    try:
        return int(pid_path.read_text().strip())
    except ValueError:
        return None


def start_daemon(args: argparse.Namespace) -> None:
    pid = _read_pid(args.pid_path)
    if pid and _pid_is_running(pid):
        print(f"Evolver daemon already running (pid={pid})")
        return

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        "--db-path",
        args.db_path,
        "--pid-path",
        str(args.pid_path),
        "--state-path",
        str(args.state_path),
        "--log-path",
        str(args.log_path),
        "--min-interval",
        str(args.min_interval),
        "--max-interval",
        str(args.max_interval),
    ]
    process = subprocess.Popen(  # noqa: S603
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    args.pid_path.write_text(str(process.pid))
    print(f"Evolver daemon started (pid={process.pid})")


def stop_daemon(args: argparse.Namespace) -> None:
    pid = _read_pid(args.pid_path)
    if not pid:
        print("Evolver daemon is not running")
        return
    if not _pid_is_running(pid):
        args.pid_path.unlink(missing_ok=True)
        print("Stale pid file removed")
        return
    os.kill(pid, signal.SIGTERM)
    time.sleep(1)
    if _pid_is_running(pid):
        os.kill(pid, signal.SIGKILL)
    args.pid_path.unlink(missing_ok=True)
    print(f"Evolver daemon stopped (pid={pid})")


def status_daemon(args: argparse.Namespace) -> None:
    pid = _read_pid(args.pid_path)
    if not pid:
        print("Evolver daemon is not running")
        return
    if _pid_is_running(pid):
        print(f"Evolver daemon is running (pid={pid})")
    else:
        print(f"Evolver daemon not running (stale pid={pid})")


def run_daemon(args: argparse.Namespace) -> None:
    daemon = EvolverDaemon(
        db_path=args.db_path,
        state_path=args.state_path,
        log_path=args.log_path,
        min_interval=args.min_interval,
        max_interval=args.max_interval,
    )
    args.pid_path.write_text(str(os.getpid()))
    daemon.run_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quant EvoMap evolver daemon")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["start", "stop", "status", "restart", "run"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--db-path", default=DEFAULT_DB_PATH)
        cmd.add_argument("--pid-path", type=Path, default=DEFAULT_PID_PATH)
        cmd.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
        cmd.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
        cmd.add_argument("--min-interval", type=int, default=300)
        cmd.add_argument("--max-interval", type=int, default=7200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "start":
        start_daemon(args)
    elif args.command == "stop":
        stop_daemon(args)
    elif args.command == "status":
        status_daemon(args)
    elif args.command == "restart":
        stop_daemon(args)
        start_daemon(args)
    elif args.command == "run":
        run_daemon(args)


if __name__ == "__main__":
    main()
