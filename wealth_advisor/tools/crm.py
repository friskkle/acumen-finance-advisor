"""Mock CRM API tool.

Simulates an external CRM service. Includes configurable failure/latency so the
system's error handling can be exercised without a real network dependency.
"""

from __future__ import annotations

import random
import time
from typing import Any

from .base import Tool, ToolResult


class CRMClient(Tool):
    name = "crm_client"
    description = "Fetch client profile and relationship notes from the CRM."

    def __init__(self, fail_rate: float = 0.0, latency: float = 0.0) -> None:
        self._fail_rate = fail_rate
        self._latency = latency
        self._data: dict[str, dict[str, Any]] = {
            "C001": {
                "advisor": "Jane Doe",
                "onboarding_year": 2019,
                "last_contact": "2024-01-10",
                "notes": "Client prefers conservative allocations; reviewing retirement plan.",
            },
            "C002": {
                "advisor": "John Smith",
                "onboarding_year": 2021,
                "last_contact": "2024-02-01",
                "notes": "High risk tolerance; interested in alternative assets.",
            },
        }

    def run(self, client_id: str, **kwargs: Any) -> ToolResult:
        time.sleep(self._latency)
        if random.random() < self._fail_rate:
            return ToolResult(
                success=False,
                error="CRM API unavailable (simulated outage)",
                source=self.name,
            )
        profile = self._data.get(client_id)
        if profile is None:
            return ToolResult(
                success=False,
                error=f"Client '{client_id}' not found in CRM",
                source=self.name,
            )
        return ToolResult(success=True, data=profile, source=self.name)
