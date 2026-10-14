"""Mock Market Data API tool.

Simulates an external market data feed for context used in advisory decisions.
"""

from __future__ import annotations

import random
import time
from typing import Any

from .base import Tool, ToolResult


class MarketDataClient(Tool):
    name = "market_data_client"
    description = "Fetch current market indicators and risk context."

    def __init__(self, fail_rate: float = 0.0, latency: float = 0.0) -> None:
        self._fail_rate = fail_rate
        self._latency = latency

    def run(self, **kwargs: Any) -> ToolResult:
        time.sleep(self._latency)
        if random.random() < self._fail_rate:
            return ToolResult(
                success=False,
                error="Market data API unavailable (simulated outage)",
                source=self.name,
            )
        data = {
            "sp500_yield": round(random.uniform(0.02, 0.05), 4),
            "treasury_10y": round(random.uniform(0.03, 0.05), 4),
            "inflation_rate": round(random.uniform(0.02, 0.04), 4),
            "volatility_index": round(random.uniform(12.0, 28.0), 2),
        }
        return ToolResult(success=True, data=data, source=self.name)
