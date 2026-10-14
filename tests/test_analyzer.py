"""Tests for the Analyzer agent and anomaly detection."""

from __future__ import annotations

import unittest

from wealth_advisor.agents.analyzer import AnalyzerAgent
from wealth_advisor.models import (
    Account,
    ClientFinancialData,
    ClientProfile,
    Transaction,
)
from wealth_advisor.state import AdvisorState


def make_data(transactions: list[Transaction], accounts: list[Account] | None = None) -> ClientFinancialData:
    return ClientFinancialData(
        client=ClientProfile(client_id="C001", name="Test"),
        accounts=accounts or [Account(id="A001", type="checking", balance=1000.0)],
        transactions=transactions,
    )


def tx(id_: str, desc: str, amount: float, date: str = "2024-01-01") -> Transaction:
    return Transaction(
        id=id_, date=date, description=desc, category="misc",
        amount=amount, account_id="A001",
    )


class TestAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = AnalyzerAgent()

    def _run(self, data: ClientFinancialData) -> list:
        state: AdvisorState = {"client_data": data}
        result = self.agent.run(state)
        return result["anomalies"]

    def test_amount_outlier(self) -> None:
        data = make_data([
            tx("1", "a", -100.0), tx("2", "b", -120.0), tx("3", "c", -110.0),
            tx("4", "d", -90.0), tx("5", "e", -5000.0),
        ])
        anomalies = self._run(data)
        self.assertTrue(any(a.category == "large_outlier_transaction" for a in anomalies))

    def test_duplicate_transaction(self) -> None:
        data = make_data([
            tx("1", "Groceries", -320.0, "2024-01-10"),
            tx("2", "Groceries", -320.0, "2024-01-11"),
        ])
        anomalies = self._run(data)
        self.assertTrue(any(a.category == "duplicate_transaction" for a in anomalies))

    def test_recurring_payment_not_duplicate(self) -> None:
        data = make_data([
            tx("1", "Rent", -1800.0, "2024-01-01"),
            tx("2", "Rent", -1800.0, "2024-02-01"),
        ])
        anomalies = self._run(data)
        self.assertFalse(any(a.category == "duplicate_transaction" for a in anomalies))

    def test_negative_balance(self) -> None:
        data = make_data(
            [tx("1", "a", -100.0), tx("2", "b", -120.0), tx("3", "c", -110.0)],
            accounts=[Account(id="A002", type="investment", balance=-50.0)],
        )
        anomalies = self._run(data)
        self.assertTrue(any(a.category == "negative_balance" for a in anomalies))

    def test_no_data_skips_analysis(self) -> None:
        state: AdvisorState = {"client_data": None}
        result = self.agent.run(state)
        self.assertNotIn("analysis", result)


if __name__ == "__main__":
    unittest.main()
