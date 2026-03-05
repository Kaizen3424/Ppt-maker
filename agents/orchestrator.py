"""Orchestrator agent - plans the presentation structure."""
import json
from typing import Dict, Any

from core.state import PresentationState
from core.config import Config, get_config
from core.llm import get_llm as get_llm_helper


def orchestrator_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Orchestrator agent plans the presentation structure.
    
    It analyzes the user's prompt and creates an initial JSON deck structure
    with slide definitions.
    """
    state["current_agent"] = "Orchestrator: Planning structure..."
    
    llm_config = config.get_llm_config("orchestrator_agent")
    proxy_config = config.get_proxy_config()
    llm = get_llm_helper(llm_config, proxy_config)
    
    prompt = state["prompt"]
    
    # Create a structured prompt for the orchestrator
    orchestration_prompt = f"""Create a slide plan for this presentation: {prompt}

Format your response as JSON with this structure:
{{"slides": [{{"title": "title", "type": "type", "key_points": ["points"], "layout_hint": "hint"}}]}}

Create 4-7 slides. Types: title, content, bullet_points, comparison, closing.
Layout hints: single column, two columns, centered, list.

Start with a title slide and end with a closing slide. Include key_points for each slide."""
    
    try:
        response = llm.invoke(orchestration_prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Try to parse JSON from response
        try:
            # Extract JSON from potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            deck_structure = json.loads(content)
            state["json_deck"] = deck_structure
        except json.JSONDecodeError:
            # Fallback: create a basic structure
            state["json_deck"] = {
                "slides": [
                    {"title": prompt, "type": "title", "key_points": [], "layout_hint": "centered"},
                    {"title": "Overview", "type": "content", "key_points": ["Main point 1", "Main point 2"], "layout_hint": "single column"},
                    {"title": "Summary", "type": "closing", "key_points": ["Key takeaway"], "layout_hint": "centered"}
                ]
            }
    except Exception as e:
        # On error, create minimal structure
        state["json_deck"] = {
            "slides": [
                {"title": prompt, "type": "title", "key_points": [], "layout_hint": "centered"},
                {"title": "Content", "type": "content", "key_points": ["Generated content"], "layout_hint": "single column"},
                {"title": "Conclusion", "type": "closing", "key_points": ["Thank you"], "layout_hint": "centered"}
            ]
        }
    
    # Initialize metadata
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["slide_count"] = len(state["json_deck"].get("slides", []))
    
    return state
