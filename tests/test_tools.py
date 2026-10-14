"""Tests for tool abstraction and mock tools."""

from __future__ import annotations

import unittest

from wealth_advisor.tools.base import ToolRegistry
from wealth_advisor.tools.crm import CRMClient
from wealth_advisor.tools.market_data import MarketDataClient


class TestToolRegistry(unittest.TestCase):
    def test_register_and_get(self) -> None:
        registry = ToolRegistry()
        registry.register(CRMClient())
        self.assertIn("crm_client", registry)
        self.assertIsInstance(registry.get("crm_client"), CRMClient)

    def test_duplicate_registration_raises(self) -> None:
        registry = ToolRegistry()
        registry.register(CRMClient())
        with self.assertRaises(ValueError):
            registry.register(CRMClient())

    def test_get_unknown_tool_raises(self) -> None:
        registry = ToolRegistry()
        with self.assertRaises(KeyError):
            registry.get("nonexistent")


class TestCRMClient(unittest.TestCase):
    def test_known_client(self) -> None:
        result = CRMClient().run(client_id="C001")
        self.assertTrue(result.success)
        self.assertEqual(result.data["advisor"], "Jane Doe")

    def test_unknown_client(self) -> None:
        result = CRMClient().run(client_id="NOPE")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error)

    def test_simulated_failure(self) -> None:
        result = CRMClient(fail_rate=1.0).run(client_id="C001")
        self.assertFalse(result.success)


class TestMarketDataClient(unittest.TestCase):
    def test_returns_indicators(self) -> None:
        result = MarketDataClient().run()
        self.assertTrue(result.success)
        self.assertIn("volatility_index", result.data)


if __name__ == "__main__":
    unittest.main()
