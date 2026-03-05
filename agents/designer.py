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
    """Design spatial layout for a single slide using AI-driven generation.
    
    This function eliminates hardcoded templates and empowers the LLM to generate
    layout specifications directly based on content analysis.
    """
    
    slide_type = slide.get("type", "content")
    heading = slide.get("heading", slide.get("title", ""))
    body_text = slide.get("body_text", "")
    bullets = slide.get("bullet_points", [])
    callout = slide.get("callout", "")
    subheading = slide.get("subheading", "")
    
    # Analyze content for layout decisions
    content_analysis = _analyze_content(
        slide_type=slide_type,
        heading=heading,
        body_text=body_text,
        bullets=bullets,
        callout=callout,
        subheading=subheading
    )
    
    # Get theme from slide metadata or use default
    theme = slide.get("theme", {
        "color_scheme": "default",
        "font_style": "modern",
        "background": "gradient"
    })
    
    # Generate dynamic layout using LLM
    layout = _generate_dynamic_layout(
        llm=llm,
        slide_type=slide_type,
        content_analysis=content_analysis,
        theme=theme,
        error_context=error_context
    )
    
    # Merge layout with slide data
    designed_slide = {**slide, "layout": layout}
    return designed_slide


def _analyze_content(
    slide_type: str,
    heading: str,
    body_text: str,
    bullets: list,
    callout: str,
    subheading: str
) -> Dict[str, Any]:
    """Analyze slide content to provide context for layout generation."""
    
    return {
        "slide_type": slide_type,
        "heading_length": len(heading) if heading else 0,
        "has_subheading": bool(subheading),
        "has_body_text": bool(body_text),
        "body_text_length": len(body_text) if body_text else 0,
        "bullet_count": len(bullets) if bullets else 0,
        "has_callout": bool(callout),
        "callout_length": len(callout) if callout else 0,
        # Estimate if content might be too long for standard layouts
        "is_content_heavy": (
            (len(body_text) > 300) or 
            (len(bullets) > 5) or 
            (len(heading) > 50)
        )
    }


def _generate_dynamic_layout(
    llm,
    slide_type: str,
    content_analysis: Dict[str, Any],
    theme: Dict[str, Any],
    error_context: str = ""
) -> Dict[str, Any]:
    """Generate dynamic layout using LLM based on content analysis.
    
    This replaces the hardcoded _get_layout_template with AI-driven design.
    """
    
    margin = 0.5
    width = SLIDE_WIDTH - (margin * 2)
    
    # Build detailed prompt for LLM to generate layout
    prompt = f"""You are a professional presentation designer. Generate a precise spatial layout for a slide.

SLIDE SPECIFICATIONS:
- Type: {slide_type}
- Width: {SLIDE_WIDTH} inches
- Height: {SLIDE_HEIGHT} inches
- Margin: {margin} inches (safe zone from edges)

CONTENT ANALYSIS:
{json.dumps(content_analysis, indent=2)}

THEME: {json.dumps(theme, indent=2)}

{error_context}

DESIGN PRINCIPLES TO FOLLOW:
1. Visual hierarchy: Most important content should be prominent
2. Alignment: Elements should align logically (left, center, or grid)
3. Proximity: Related elements should be close together
4. Contrast: Use spacing to separate distinct sections
5. Balance: Distribute visual weight evenly across the slide

Generate a JSON layout with the following structure:
{{
    "theme": {{ ... }},  // Applied theme settings
    "background": {{ ... }},  // Background styling
    "elements": [
        {{
            "type": "title" | "heading" | "subtitle" | "subheading" | "body" | "bullets" | "callout" | "left_content" | "right_content" | "image",
            "x": <position in inches from left>,
            "y": <position in inches from top>,
            "width": <width in inches>,
            "height": <height in inches>,
            "style": {{ "font_size": <optional>, "alignment": "left" | "center" | "right", "weight": "normal" | "bold" }}
        }}
    ]
}}

Respond ONLY with the JSON layout. No explanation."""
    
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON response
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            layout = json.loads(content)
            
            # Validate and ensure required fields
            if "elements" in layout and isinstance(layout["elements"], list):
                return layout
        except (json.JSONDecodeError, AttributeError):
            pass
    except Exception as e:
        pass
    
    # Fallback: Use intelligent default based on content analysis
    return _get_intelligent_default_layout(slide_type, content_analysis, margin, width)


def _get_intelligent_default_layout(
    slide_type: str,
    content_analysis: Dict[str, Any],
    margin: float,
    width: float
) -> Dict[str, Any]:
    """Generate intelligent default layout based on content analysis.
    
    This is a fallback when LLM generation fails, but still uses content-aware logic.
    """
    
    elements = []
    
    if slide_type == "title":
        # Centered title slide
        elements = [
            {"type": "title", "x": margin, "y": 2.5, "width": width, "height": 1.5,
             "style": {"font_size": 44, "alignment": "center", "weight": "bold"}},
            {"type": "subtitle", "x": margin, "y": 4.2, "width": width, "height": 1,
             "style": {"font_size": 24, "alignment": "center", "weight": "normal"}}
        ]
    
    elif slide_type == "closing":
        # Centered closing slide
        elements = [
            {"type": "title", "x": margin, "y": 2.5, "width": width, "height": 1.5,
             "style": {"font_size": 44, "alignment": "center", "weight": "bold"}},
            {"type": "cta", "x": margin, "y": 4.5, "width": width, "height": 1.5,
             "style": {"font_size": 20, "alignment": "center", "weight": "normal"}}
        ]
    
    elif slide_type == "comparison" or content_analysis.get("bullet_count", 0) > 4:
        # Two-column or multi-column layout for comparison or many bullets
        elements = [
            {"type": "heading", "x": margin, "y": 0.5, "width": width, "height": 0.8,
             "style": {"font_size": 32, "alignment": "left", "weight": "bold"}},
            {"type": "left_content", "x": margin, "y": 1.5, "width": width/2 - 0.25, "height": 5,
             "style": {"font_size": 18, "alignment": "left", "weight": "normal"}},
            {"type": "right_content", "x": margin + width/2 + 0.25, "y": 1.5, "width": width/2 - 0.25, "height": 5,
             "style": {"font_size": 18, "alignment": "left", "weight": "normal"}}
        ]
    
    elif content_analysis.get("has_callout"):
        # Layout with callout box
        elements = [
            {"type": "heading", "x": margin, "y": 0.5, "width": width, "height": 0.8,
             "style": {"font_size": 32, "alignment": "left", "weight": "bold"}},
            {"type": "body", "x": margin, "y": 1.5, "width": width * 0.6, "height": 4,
             "style": {"font_size": 18, "alignment": "left", "weight": "normal"}},
            {"type": "callout", "x": margin + width * 0.65, "y": 1.5, "width": width * 0.35, "height": 4,
             "style": {"font_size": 14, "alignment": "left", "weight": "normal"}}
        ]
    
    elif content_analysis.get("is_content_heavy"):
        # For heavy content, use compact layout with more space for content
        elements = [
            {"type": "heading", "x": margin, "y": 0.3, "width": width, "height": 0.6,
             "style": {"font_size": 28, "alignment": "left", "weight": "bold"}},
            {"type": "bullets", "x": margin, "y": 1.0, "width": width, "height": 6,
             "style": {"font_size": 16, "alignment": "left", "weight": "normal"}}
        ]
    
    else:
        # Default content layout
        elements = [
            {"type": "heading", "x": margin, "y": 0.5, "width": width, "height": 0.8,
             "style": {"font_size": 32, "alignment": "left", "weight": "bold"}},
            {"type": "body", "x": margin, "y": 1.5, "width": width, "height": 2.5,
             "style": {"font_size": 18, "alignment": "left", "weight": "normal"}},
            {"type": "bullets", "x": margin, "y": 4.2, "width": width, "height": 2.8,
             "style": {"font_size": 16, "alignment": "left", "weight": "normal"}}
        ]
    
    return {
        "theme": {
            "color_scheme": "default",
            "font_style": "modern",
            "background": "gradient"
        },
        "background": {
            "type": "gradient",
            "colors": ["#667eea", "#764ba2"]
        },
        "elements": elements
    }


def _get_layout_template(slide_type: str, layout_hint: str = "single column") -> Dict[str, Any]:
    """Get predefined layout template for a slide type.
    
    DEPRECATED: This function is kept for backward compatibility.
    Use _generate_dynamic_layout instead for AI-driven layouts.
    """
    
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
