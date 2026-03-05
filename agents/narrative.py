"""Narrative agent - creates compelling content for each slide."""
import json
from typing import Dict, Any

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper


def narrative_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Narrative agent creates compelling content for each slide.
    
    It takes the structured slide plan and research context, then generates
    the actual content (headings, body text, bullet points) for each slide.
    """
    state["current_agent"] = "Narrative: Writing compelling content..."
    
    prompt = state["prompt"]
    slides = state["json_deck"].get("slides", [])
    research_context = state["metadata"].get("research_context", {})
    key_insights = state["metadata"].get("key_insights", [])
    
    llm_config = config.get_llm_config("narrative_agent")
    proxy_config = config.get_proxy_config()
    llm = get_llm_helper(llm_config, proxy_config)
    
    # Generate content for each slide
    enriched_slides = []
    
    for i, slide in enumerate(slides):
        slide_content = _generate_slide_content(
            llm=llm,
            slide=slide,
            prompt=prompt,
            research_context=research_context,
            key_insights=key_insights,
            slide_index=i
        )
        enriched_slides.append(slide_content)
    
    state["json_deck"]["slides"] = enriched_slides
    
    return state


def _generate_slide_content(
    llm,
    slide: Dict[str, Any],
    prompt: str,
    research_context: Dict[str, Any],
    key_insights: list,
    slide_index: int
) -> Dict[str, Any]:
    """Generate content for a single slide using the LLM."""
    
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    existing_points = slide.get("key_points", [])
    
    # Build context for the LLM
    context_parts = [f"Presentation topic: {prompt}"]
    if key_insights:
        context_parts.append(f"Key research insights: {'; '.join(key_insights[:5])}")
    context = "\n".join(context_parts)
    
    if slide_type == "title":
        # Title slides need minimal content
        return {
            "title": title,
            "type": slide_type,
            "heading": title,
            "subheading": prompt,
            "key_points": existing_points,
            "layout_hint": slide.get("layout_hint", "centered")
        }
    
    # For content slides, generate detailed text
    content_prompt = f"""Topic: {prompt}
Title: {title}
Type: {slide_type}

Create JSON with:
- heading: main heading
- body_text: 2-3 sentences
- bullet_points: 3-4 bullet points as array
- callout: optional quote

Output only JSON."""
    
    try:
        response = llm.invoke(content_prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse JSON response
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            generated = json.loads(content)
            
            return {
                "title": title,
                "type": slide_type,
                "heading": generated.get("heading", title),
                "body_text": generated.get("body_text", ""),
                "bullet_points": generated.get("bullet_points", existing_points),
                "callout": generated.get("callout"),
                "key_points": generated.get("bullet_points", existing_points),
                "layout_hint": slide.get("layout_hint", "single column")
            }
        except (json.JSONDecodeError, AttributeError):
            pass
    except Exception:
        pass
    
    # Fallback: return slide with existing data
    return {
        "title": title,
        "type": slide_type,
        "heading": title,
        "body_text": "",
        "bullet_points": existing_points,
        "key_points": existing_points,
        "layout_hint": slide.get("layout_hint", "single column")
    }
