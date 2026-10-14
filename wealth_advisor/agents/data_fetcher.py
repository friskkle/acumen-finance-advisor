"""Data Fetcher agent: retrieves and prepares data from inputs and external APIs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseAgent
from ..models import ClientFinancialData
from ..state import AdvisorState


class DataFetcherAgent(BaseAgent):
    name = "data_fetcher"

    def run(self, state: AdvisorState) -> dict[str, Any]:
        errors = list(state.get("errors", []))
        log_entries = list(state.get("execution_log", []))

        client_data = self._load_client_data(state.get("input") or {}, errors, log_entries)

        crm_data = self._fetch_crm(state.get("client_id"), errors, log_entries)
        market_data = self._fetch_market(errors, log_entries)

        update: dict[str, Any] = {
            "client_data": client_data,
            "crm_data": crm_data,
            "market_data": market_data,
            "errors": errors,
            "execution_log": log_entries,
        }
        return update

    def _load_client_data(
        self,
        input_payload: dict[str, Any],
        errors: list[dict[str, Any]],
        log_entries: list[dict[str, Any]],
    ) -> ClientFinancialData | None:
        raw = input_payload.get("financial_data")
        if raw is None:
            path = input_payload.get("financial_data_path")
            if path and Path(path).exists():
                raw = json.loads(Path(path).read_text(encoding="utf-8"))

        if raw is None:
            self.log("No financial data provided")
            errors.append({"agent": self.name, "message": "No financial data available"})
            return None

        try:
            data = ClientFinancialData.model_validate(raw)
            self.log(f"Loaded financial data for {data.client.client_id}")
            log_entries.append({"agent": self.name, "action": "load_client_data", "status": "ok"})
            return data
        except Exception as exc:
            self.log(f"Failed to parse client data: {exc}")
            errors.append({"agent": self.name, "message": f"Invalid financial data: {exc}"})
            return None

    def _fetch_crm(
        self,
        client_id: str | None,
        errors: list[dict[str, Any]],
        log_entries: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if client_id is None or "crm_client" not in self.tools:
            return None
        result = self.tools.get("crm_client").run(client_id=client_id)
        if result.success:
            self.log("Fetched CRM context")
            log_entries.append({"agent": self.name, "action": "fetch_crm", "status": "ok"})
            return result.data
        self.log(f"CRM fetch failed: {result.error}")
        errors.append({"agent": self.name, "message": result.error})
        log_entries.append({"agent": self.name, "action": "fetch_crm", "status": "failed"})
        return None

    def _fetch_market(
        self,
        errors: list[dict[str, Any]],
        log_entries: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if "market_data_client" not in self.tools:
            return None
        result = self.tools.get("market_data_client").run()
        if result.success:
            self.log("Fetched market data")
            log_entries.append({"agent": self.name, "action": "fetch_market", "status": "ok"})
            return result.data
        self.log(f"Market data fetch failed: {result.error}")
        errors.append({"agent": self.name, "message": result.error})
        log_entries.append({"agent": self.name, "action": "fetch_market", "status": "failed"})
        return None
