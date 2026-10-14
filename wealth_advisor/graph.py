"""LangGraph workflow: wires agents into an executable state graph."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from .agents import AdvisorAgent, AnalyzerAgent, DataFetcherAgent, OrchestratorAgent
from .state import AdvisorState
from .tools.base import ToolRegistry


def build_graph(tools: ToolRegistry) -> Any:
    orchestrator = OrchestratorAgent()
    fetcher = DataFetcherAgent(tools=tools)
    analyzer = AnalyzerAgent()
    advisor = AdvisorAgent()

    graph = StateGraph(AdvisorState)

    graph.add_node("orchestrate", orchestrator.run)
    graph.add_node("fetch_data", fetcher.run)
    graph.add_node("analyze", analyzer.run)
    graph.add_node("generate_advisory", advisor.run)

    graph.add_edge(START, "orchestrate")
    graph.add_edge("orchestrate", "fetch_data")
    graph.add_edge("fetch_data", "analyze")
    graph.add_edge("analyze", "generate_advisory")
    graph.add_edge("generate_advisory", END)

    return graph.compile()
