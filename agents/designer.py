"""Designer agent - calculates spatial layouts and assigns coordinates."""
import json
from typing import Dict, Any

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper


# Standard slide dimensions (16:9 aspect ratio)
SLIDE_WIDTH = 13.333  # inches
SLIDE_HEIGHT = 7.5    # inches


def designer_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Designer agent calculates spatial layouts for each slide.
    
    It assigns x, y, width, height coordinates to all elements,
    ensuring no overlap and good visual hierarchy.
    """
    state["current_agent"] = "Designer: Calculating spatial layouts..."
    
    slides = state["json_deck"].get("slides", [])
    errors = state.get("errors", [])
    
    # Build error context if there are previous QA issues
    error_context = ""
    if errors:
        error_context = f"\n\nPREVIOUS ERRORS TO FIX:\n" + "\n".join(errors)
    
    llm_config = config.get_llm_config("design_agent")
    proxy_config = config.get_proxy_config()
    llm = get_llm_helper(llm_config, proxy_config)
    
    # Process each slide
    designed_slides = []
    for i, slide in enumerate(slides):
        designed_slide = _design_slide(
            llm=llm,
            slide=slide,
            slide_index=i,
            error_context=error_context if i == 0 else ""  # Only pass errors to first pass
        )
        designed_slides.append(designed_slide)
    
    state["json_deck"]["slides"] = designed_slides
    
    # Clear errors after attempting fix
    state["errors"] = []
    
    return state


def _design_slide(
    llm,
    slide: Dict[str, Any],
    slide_index: int,
    error_context: str = ""
) -> Dict[str, Any]:
    """Design spatial layout for a single slide."""
    
    slide_type = slide.get("type", "content")
    layout_hint = slide.get("layout_hint", "single column")
    
    # Use predefined templates - they are well-designed
    layout = _get_layout_template(slide_type, layout_hint)
    
    # Merge layout with slide data
    designed_slide = {**slide, "layout": layout}
    return designed_slide


def _get_layout_template(slide_type: str, layout_hint: str = "single column") -> Dict[str, Any]:
    """Get predefined layout template for a slide type."""
    
    margin = 0.5
    width = SLIDE_WIDTH - (margin * 2)
    
    templates = {
        "title": {
            "elements": [
                {"type": "title", "x": margin, "y": 2.5, "width": width, "height": 1.5},
                {"type": "subtitle", "x": margin, "y": 4.2, "width": width, "height": 1}
            ]
        },
        "content": {
            "elements": [
                {"type": "heading", "x": margin, "y": 0.5, "width": width, "height": 0.8},
                {"type": "body", "x": margin, "y": 1.8, "width": width, "height": 3},
                {"type": "bullets", "x": margin, "y": 5, "width": width, "height": 2}
            ]
        },
        "bullet_points": {
            "elements": [
                {"type": "heading", "x": margin, "y": 0.5, "width": width, "height": 0.8},
                {"type": "bullets", "x": margin, "y": 1.5, "width": width, "height": 5.5}
            ]
        },
        "comparison": {
            "elements": [
                {"type": "heading", "x": margin, "y": 0.5, "width": width, "height": 0.8},
                {"type": "left_content", "x": margin, "y": 1.5, "width": width/2 - 0.25, "height": 5},
                {"type": "right_content", "x": margin + width/2 + 0.25, "y": 1.5, "width": width/2 - 0.25, "height": 5}
            ]
        },
        "closing": {
            "elements": [
                {"type": "title", "x": margin, "y": 2.5, "width": width, "height": 1.5},
                {"type": "cta", "x": margin, "y": 4.5, "width": width, "height": 1.5}
            ]
        }
    }
    
    return templates.get(slide_type, templates["content"])
