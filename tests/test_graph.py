"""End-to-end tests for the LangGraph workflow and error handling."""

from __future__ import annotations

import unittest

from wealth_advisor.graph import build_graph
from wealth_advisor.main import build_tool_registry


class TestWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = build_graph(build_tool_registry())

    def test_full_flow_produces_advisory(self) -> None:
        result = self.graph.invoke(
            {"input": {"client_id": "C001", "financial_data_path": "data/sample_client.json"}}
        )
        self.assertIsNotNone(result["advisory"])
        self.assertEqual(result["advisory"].client_id, "C001")
        self.assertGreaterEqual(len(result["advisory"].anomalies), 1)

    def test_missing_client_id_records_error(self) -> None:
        result = self.graph.invoke({"input": {}})
        self.assertTrue(any(e["message"] == "Missing client_id in input" for e in result["errors"]))

    def test_missing_data_produces_fallback_advisory(self) -> None:
        result = self.graph.invoke({"input": {"client_id": "C002"}})
        self.assertIsNotNone(result["advisory"])
        self.assertIn("could not be completed", result["advisory"].summary)


if __name__ == "__main__":
    unittest.main()
