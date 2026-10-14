"""Orchestrator agent: central coordinator and router."""

from __future__ import annotations

from typing import Any

from .base import BaseAgent
from ..state import AdvisorState


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    def run(self, state: AdvisorState) -> dict[str, Any]:
        client_id = state.get("client_id") or (state.get("input") or {}).get("client_id")
        if not client_id:
            self.log("No client_id provided; routing to error path")
            return {
                "client_id": None,
                "errors": [{"agent": self.name, "message": "Missing client_id in input"}],
            }

        self.log(f"Orchestrating workflow for client {client_id}")
        log_entries = state.get("execution_log", [])
        log_entries.append(
            {
                "agent": self.name,
                "action": "route",
                "client_id": client_id,
                "plan": ["fetch_data", "analyze", "generate_advisory"],
            }
        )
        return {"client_id": client_id, "execution_log": log_entries}
