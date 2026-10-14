"""CLI entry point for the Wealth Advisor Assistant."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*allowed_objects.*")

from .graph import build_graph
from .logging_setup import configure_logging, get_logger
from .tools.base import ToolRegistry
from .tools.crm import CRMClient
from .tools.market_data import MarketDataClient

logger = get_logger("main")


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CRMClient())
    registry.register(MarketDataClient())
    return registry


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wealth Advisor Assistant")
    parser.add_argument(
        "--client-data",
        type=str,
        default="data/sample_client.json",
        help="Path to client financial data JSON file",
    )
    parser.add_argument("--client-id", type=str, help="Client ID override (optional)")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    return parser.parse_args(argv)


def load_input(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.client_data)
    if not path.exists():
        logger.error(f"Client data file not found: {path}")
        sys.exit(1)
    raw = json.loads(path.read_text(encoding="utf-8"))
    payload: dict[str, Any] = {"financial_data": raw}
    if args.client_id:
        payload["client_id"] = args.client_id
    else:
        payload["client_id"] = raw.get("client", {}).get("client_id")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    configure_logging(level=getattr(__import__("logging"), args.log_level.upper()))

    payload = load_input(args)
    registry = build_tool_registry()
    graph = build_graph(registry)

    logger.info(f"Running workflow for client {payload.get('client_id')}")
    result = graph.invoke({"input": payload})

    advisory = result.get("advisory")
    output = {
        "advisory": advisory.model_dump() if advisory else None,
        "errors": result.get("errors", []),
        "execution_log": result.get("execution_log", []),
    }
    print(json.dumps(output, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
