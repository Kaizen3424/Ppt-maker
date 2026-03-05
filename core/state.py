"""Core state definitions for the presentation agent."""
from typing import TypedDict, List, Dict, Any


class PresentationState(TypedDict):
    """The universal state that flows through all agents."""
    prompt: str
    metadata: Dict[str, Any]
    json_deck: Dict[str, Any]
    errors: List[str]
    current_agent: str  # Used for CLI UI updates
