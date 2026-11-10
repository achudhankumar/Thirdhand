"""Thirdhand System Prompt, Station Code Mapper & LLM Router (Playbook Section 6.B)."""

from services.llm_orchestrator import (
    SYSTEM_PROMPT,
    LLMOrchestrator,
    normalize_audio,
    tool_schemas,
)
from services.tools.transit_tool import AIRPORTS, STATIONS, airport_code, station_code

THIRDHAND_SYSTEM_PROMPT = SYSTEM_PROMPT

# Alias LLMRouter to LLMOrchestrator so imports from either module name work seamlessly
LLMRouter = LLMOrchestrator

__all__ = [
    "THIRDHAND_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
    "LLMRouter",
    "LLMOrchestrator",
    "STATIONS",
    "AIRPORTS",
    "station_code",
    "airport_code",
    "normalize_audio",
    "tool_schemas",
]
