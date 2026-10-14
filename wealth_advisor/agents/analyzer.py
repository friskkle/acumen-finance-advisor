"""Analyzer agent: financial analysis and anomaly detection."""

from __future__ import annotations

import statistics
from datetime import date, datetime
from typing import Any

from .base import BaseAgent
from ..models import AnalysisResult, Anomaly, ClientFinancialData, Severity
from ..state import AdvisorState

ANOMALY_THRESHOLDS = {
    "amount_robust_zscore": 3.5,
    "duplicate_window_days": 2,
    "large_transaction_ratio": 0.3,
}


class AnalyzerAgent(BaseAgent):
    name = "analyzer"

    def run(self, state: AdvisorState) -> dict[str, Any]:
        client_data = state.get("client_data")
        errors = list(state.get("errors", []))
        log_entries = list(state.get("execution_log", []))

        if client_data is None:
            self.log("Skipping analysis: no client data available")
            return {"errors": errors, "execution_log": log_entries}

        analysis = self._analyze(client_data)
        self.log(f"Analysis complete: {len(analysis.anomalies)} anomalies detected")
        log_entries.append(
            {"agent": self.name, "action": "analyze", "anomalies": len(analysis.anomalies)}
        )
        return {
            "analysis": analysis,
            "anomalies": analysis.anomalies,
            "errors": errors,
            "execution_log": log_entries,
        }

    def _analyze(self, data: ClientFinancialData) -> AnalysisResult:
        transactions = data.transactions

        income = sum(t.amount for t in transactions if t.amount > 0)
        expenses = sum(-t.amount for t in transactions if t.amount < 0)
        net = income - expenses

        category_totals: dict[str, float] = {}
        for t in transactions:
            if t.amount < 0:
                category_totals[t.category] = category_totals.get(t.category, 0.0) + (-t.amount)

        top_categories = sorted(
            [{"category": k, "total": round(v, 2)} for k, v in category_totals.items()],
            key=lambda x: x["total"],
            reverse=True,
        )[:5]

        anomalies = self._detect_anomalies(data)

        return AnalysisResult(
            total_income=round(income, 2),
            total_expenses=round(expenses, 2),
            net_savings=round(net, 2),
            top_spending_categories=top_categories,
            anomalies=anomalies,
        )

    def _detect_anomalies(self, data: ClientFinancialData) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        anomalies.extend(self._amount_outliers(data))
        anomalies.extend(self._duplicate_transactions(data))
        anomalies.extend(self._low_balance(data))
        return anomalies

    def _amount_outliers(self, data: ClientFinancialData) -> list[Anomaly]:
        outflows = [t for t in data.transactions if t.amount < 0]
        if len(outflows) < 3:
            return []

        amounts = [-t.amount for t in outflows]
        median = statistics.median(amounts)
        mad = statistics.median([abs(a - median) for a in amounts])

        threshold = ANOMALY_THRESHOLDS["amount_robust_zscore"]
        result: list[Anomaly] = []
        for t in outflows:
            amt = -t.amount
            if mad == 0:
                score = 0.0
            else:
                score = 0.6745 * (amt - median) / mad
            if score > threshold:
                severity = Severity.HIGH if score > threshold * 2 else Severity.MEDIUM
                result.append(
                    Anomaly(
                        category="large_outlier_transaction",
                        severity=severity,
                        description=f"Unusually large outflow of ${amt:,.2f} for '{t.description}'",
                        details={"transaction_id": t.id, "robust_zscore": round(score, 2)},
                    )
                )
        return result

    def _duplicate_transactions(self, data: ClientFinancialData) -> list[Anomaly]:
        window = ANOMALY_THRESHOLDS["duplicate_window_days"]
        seen: dict[tuple[str, float], tuple[str, date]] = {}
        result: list[Anomaly] = []
        for t in data.transactions:
            if t.amount >= 0:
                continue
            tx_date = self._parse_date(t.date)
            if tx_date is None:
                continue
            key = (t.description.strip().lower(), round(t.amount, 2))
            if key in seen:
                first_id, first_date = seen[key]
                if (tx_date - first_date).days <= window:
                    result.append(
                        Anomaly(
                            category="duplicate_transaction",
                            severity=Severity.MEDIUM,
                            description=f"Possible duplicate transaction: '{t.description}' for ${-t.amount:,.2f}",
                            details={
                                "transaction_id": t.id,
                                "first_occurrence": first_id,
                            },
                        )
                    )
            else:
                seen[key] = (t.id, tx_date)
        return result

    @staticmethod
    def _parse_date(value: str) -> date | None:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _low_balance(self, data: ClientFinancialData) -> list[Anomaly]:
        result: list[Anomaly] = []
        for account in data.accounts:
            if account.balance < 0:
                result.append(
                    Anomaly(
                        category="negative_balance",
                        severity=Severity.HIGH,
                        description=f"Account '{account.id}' has a negative balance of ${account.balance:,.2f}",
                        details={"account_id": account.id, "balance": account.balance},
                    )
                )
        return result
