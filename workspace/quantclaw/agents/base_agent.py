#!/usr/bin/env python3
"""
Base agent utilities for Quant EvoMap multi-agent workers.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentConfig:
    agent_id: str
    role: str
    api_base: str = "http://127.0.0.1:8889/api/v1"
    poll_interval: int = 30


class BaseAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.running = True

    def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.config.api_base}{path}"
        body = None
        headers = {"Content-Type": "application/json"}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8")
            raise RuntimeError(f"HTTP {exc.code} {url}: {payload}") from exc

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if params:
            encoded = urllib.parse.urlencode(params)
            return self._request("GET", f"{path}?{encoded}")
        return self._request("GET", path)

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", path, payload)

    def claim_next_bounty(self, task_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        bounties = self.get("/bounties", {"status": "pending"}).get("items", [])
        for bounty in bounties:
            if task_type and bounty.get("task_type") != task_type:
                continue
            try:
                self.post(f"/bounties/{bounty['task_id']}/claim", {"agent_id": self.config.agent_id})
                return bounty
            except RuntimeError:
                continue
        return None

    def run_once(self) -> Dict[str, Any]:
        raise NotImplementedError

    def run_forever(self) -> None:
        while self.running:
            try:
                result = self.run_once()
                print(json.dumps({"agent": self.config.agent_id, "result": result}, ensure_ascii=True))
            except Exception as exc:  # pylint: disable=broad-except
                print(json.dumps({"agent": self.config.agent_id, "error": str(exc)}, ensure_ascii=True))
            time.sleep(self.config.poll_interval)


def common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--api-base", default="http://127.0.0.1:8889/api/v1")
    parser.add_argument("--poll-interval", type=int, default=30)
    parser.add_argument("--once", action="store_true")
    return parser
