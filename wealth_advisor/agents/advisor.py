"""Advisor agent: produces structured advisory output from analysis."""

from __future__ import annotations

from typing import Any

from .base import BaseAgent
from ..models import AdvisoryOutput, AnalysisResult
from ..state import AdvisorState


class AdvisorAgent(BaseAgent):
    name = "advisor"

    def run(self, state: AdvisorState) -> dict[str, Any]:
        analysis: AnalysisResult | None = state.get("analysis")
        client_id = state.get("client_id") or "unknown"
        errors = list(state.get("errors", []))
        log_entries = list(state.get("execution_log", []))

        if analysis is None:
            self.log("No analysis available; producing fallback advisory")
            advisory = AdvisoryOutput(
                client_id=client_id,
                summary="Analysis could not be completed due to missing data.",
                insights=[],
                anomalies=[],
                recommendations=["Review input data and re-run the workflow."],
            )
            return {
                "advisory": advisory,
                "errors": errors,
                "execution_log": log_entries,
            }

        anomalies = analysis.anomalies
        insights = self._build_insights(analysis)
        recommendations = self._build_recommendations(analysis, anomalies)

        advisory = AdvisoryOutput(
            client_id=client_id,
            summary=(
                f"Net savings of ${analysis.net_savings:,.2f} "
                f"(income ${analysis.total_income:,.2f}, expenses ${analysis.total_expenses:,.2f}). "
                f"{len(anomalies)} anomaly(ies) detected."
            ),
            insights=insights,
            anomalies=anomalies,
            recommendations=recommendations,
        )

        self.log(f"Generated advisory for client {client_id}")
        log_entries.append({"agent": self.name, "action": "generate_advisory", "status": "ok"})
        return {
            "advisory": advisory,
            "errors": errors,
            "execution_log": log_entries,
        }

    def _build_insights(self, analysis: AnalysisResult) -> list[str]:
        insights = []
        if analysis.top_spending_categories:
            top = analysis.top_spending_categories[0]
            insights.append(
                f"Top spending category is '{top['category']}' at ${top['total']:,.2f}."
            )
        if analysis.net_savings < 0:
            insights.append("Client is spending more than they earn.")
        else:
            insights.append("Client maintains a positive savings rate.")
        return insights

    def _build_recommendations(
        self, analysis: AnalysisResult, anomalies: list[Any]
    ) -> list[str]:
        recs = []
        if analysis.net_savings < 0:
            recs.append("Consider a budget review to reduce expenses.")
        if any(a.category == "negative_balance" for a in anomalies):
            recs.append("Address negative account balances immediately.")
        if any(a.category == "large_outlier_transaction" for a in anomalies):
            recs.append("Review unusually large transactions with the client.")
        if any(a.category == "duplicate_transaction" for a in anomalies):
            recs.append("Verify possible duplicate charges and request refunds if needed.")
        if not recs:
            recs.append("No urgent actions identified; continue standard monitoring.")
        return recs
