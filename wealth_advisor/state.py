"""Shared state for the LangGraph workflow.

The state is a plain dictionary of typed fields that flows through every node.
Each agent reads from and writes back to this shared state.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from .models import AdvisoryOutput, AnalysisResult, Anomaly, ClientFinancialData


class AdvisorState(TypedDict, total=False):
    input: dict[str, Any]
    client_id: Optional[str]
    client_data: Optional[ClientFinancialData]
    crm_data: Optional[dict[str, Any]]
    market_data: Optional[dict[str, Any]]
    analysis: Optional[AnalysisResult]
    anomalies: list[Anomaly]
    advisory: Optional[AdvisoryOutput]
    errors: list[dict[str, Any]]
    execution_log: list[dict[str, Any]]
