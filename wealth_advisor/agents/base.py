"""Base agent abstraction.

Every specialized agent implements a single ``run`` method that takes the shared
state and returns a partial update (a dict merged back into the state).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..state import AdvisorState
from ..tools.base import ToolRegistry


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, tools: Optional[ToolRegistry] = None) -> None:
        self.tools = tools or ToolRegistry()
        self.logger = logging.getLogger(f"agent.{self.name}")

    def log(self, message: str, **extra: Any) -> None:
        self.logger.info(message)

    @abstractmethod
    def run(self, state: AdvisorState) -> dict[str, Any]:
        raise NotImplementedError
