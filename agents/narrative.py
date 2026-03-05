"""Narrative agent - creates compelling content for each slide."""
import json
from typing import Dict, Any, List, Optional

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper


# Supported rhetorical structures
RHETORICAL_STRUCTURES = {
    "problem_solution": {
        "description": "Presents a problem and offers solutions",
        "flow": ["context", "problem", "solution", "benefits"]
    },
    "cause_effect": {
        "description": "Explains causes and their effects",
        "flow": ["context", "cause", "effect", "implications"]
    },
    "chronological": {
        "description": "Timeline-based narrative",
        "flow": ["background", "timeline", "current", "future"]
    },
    "comparison": {
        "description": "Compares and contrasts options",
        "flow": ["option_a", "option_b", "comparison", "recommendation"]
    },
    "general": {
        "description": "General narrative flow",
        "flow": ["introduction", "main_points", "conclusion"]
    }
}

# Tone presets
TONE_PRESETS = {
    "professional": {
        "vocabulary": "formal business language",
        "sentence_structure": "clear and concise",
        "style": "authoritative but accessible"
    },
    "academic": {
        "vocabulary": "research-oriented terminology",
        "sentence_structure": "complex but precise",
        "style": "objective and analytical"
    },
    "casual": {
        "vocabulary": "conversational language",
        "sentence_structure": "short and engaging",
        "style": "friendly and approachable"
    },
    "technical": {
        "vocabulary": "technical jargon",
        "sentence_structure": "detailed and precise",
        "style": "factual and exact"
    },
    "persuasive": {
        "vocabulary": "compelling and action-oriented",
        "sentence_structure": "varied for impact",
        "style": "convincing and motivational"
    }
}

# Audience presets
AUDIENCE_PRESETS = {
    "executives": {
        "focus": "high-level insights and business impact",
        "detail_level": "minimal technical detail",
        "key_concerns": "ROI, strategy, competitive advantage"
    },
    "technicians": {
        "focus": "technical implementation and architecture",
        "detail_level": "comprehensive technical detail",
        "key_concerns": "feasibility, implementation, integration"
    },
    "general": {
        "focus": "clear explanations and key takeaways",
        "detail_level": "balanced overview",
        "key_concerns": "understanding and relevance"
    },
    "students": {
        "focus": "educational content and learning",
        "detail_level": "foundational explanations",
        "key_concerns": "clarity and learning value"
    },
    "investors": {
        "focus": "market opportunity and growth potential",
        "detail_level": "high-level metrics and projections",
        "key_concerns": "ROI, market size, competitive edge"
    }
}


def narrative_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Narrative agent creates compelling content for each slide.
    
    It takes the structured slide plan and research context, then generates
    the actual content (headings, body text, bullet points) for each slide.
    
    Enhanced with:
    - Deeper research synthesis
    - Structured content generation with rhetorical structures
    - Tone and audience adaptation
    - Data-to-text generation for numerical insights
    """
    state["current_agent"] = "Narrative: Writing compelling content..."
    
    prompt = state["prompt"]
    slides = state["json_deck"].get("slides", [])
    research_context = state["metadata"].get("research_context", {})
    key_insights = state["metadata"].get("key_insights", [])
    
    # Get narrative customization parameters
    narrative_config = config._config.get("narrative", {})
    target_tone = narrative_config.get("tone", "professional")
    target_audience = narrative_config.get("audience", "general")
    rhetorical_structure = narrative_config.get("structure", "general")
    
    llm_config = config.get_llm_config("narrative_agent")
    proxy_config = config.get_proxy_config()
    llm = get_llm_helper(llm_config, proxy_config)
    
    # Get tone and audience presets
    tone = TONE_PRESETS.get(target_tone, TONE_PRESETS["professional"])
    audience = AUDIENCE_PRESETS.get(target_audience, AUDIENCE_PRESETS["general"])
    structure = RHETORICAL_STRUCTURES.get(rhetorical_structure, RHETORICAL_STRUCTURES["general"])
    
    # Generate content for each slide
    enriched_slides = []
    
    for i, slide in enumerate(slides):
        slide_content = _generate_slide_content(
            llm=llm,
            slide=slide,
            prompt=prompt,
            research_context=research_context,
            key_insights=key_insights,
            slide_index=i,
            tone=tone,
            audience=audience,
            structure=structure
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
    slide_index: int,
    tone: Dict[str, Any],
    audience: Dict[str, Any],
    structure: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate content for a single slide using the LLM with enhanced prompts."""
    
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    existing_points = slide.get("key_points", [])
    
    # Get any numerical data from slide
    numerical_data = slide.get("data", {})
    
    # Build enhanced context for the LLM
    context_parts = [
        f"Presentation topic: {prompt}",
        f"Target audience: {audience['focus']}",
        f"Focus concerns: {audience['key_concerns']}",
    ]
    
    if key_insights:
        # Deeper research integration - synthesize information
        context_parts.append(f"Key research insights: {'; '.join(key_insights[:7])}")
    
    # Include research context for deeper synthesis
    if research_context:
        context_parts.append(f"Research context: {json.dumps(research_context)[:500]}...")
    
    context = "\n".join(context_parts)
    
    if slide_type == "title":
        # Title slides need minimal content
        return {
            "title": title,
            "type": slide_type,
            "heading": title,
            "subheading": prompt,
            "key_points": existing_points,
            "layout_hint": slide.get("layout_hint", "centered"),
            "tone": tone,
            "audience": audience
        }
    
    # For content slides, generate detailed text with enhanced prompting
    content_prompt = _build_enhanced_content_prompt(
        prompt=prompt,
        title=title,
        slide_type=slide_type,
        context=context,
        existing_points=existing_points,
        numerical_data=numerical_data,
        tone=tone,
        audience=audience,
        structure=structure
    )
    
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
                "layout_hint": slide.get("layout_hint", "single column"),
                "data_insight": generated.get("data_insight"),  # Data-to-text generation
                "tone": tone,
                "audience": audience
            }
        except (json.JSONDecodeError, AttributeError):
            pass
    except Exception as e:
        pass
    
    # Fallback: return slide with existing data
    return {
        "title": title,
        "type": slide_type,
        "heading": title,
        "body_text": "",
        "bullet_points": existing_points,
        "key_points": existing_points,
        "layout_hint": slide.get("layout_hint", "single column"),
        "tone": tone,
        "audience": audience
    }


def _build_enhanced_content_prompt(
    prompt: str,
    title: str,
    slide_type: str,
    context: str,
    existing_points: list,
    numerical_data: dict,
    tone: Dict[str, Any],
    audience: Dict[str, Any],
    structure: Dict[str, Any]
) -> str:
    """Build an enhanced prompt for content generation with all customization options."""
    
    # Build the prompt with all parameters
    prompt_parts = [
        f"""Topic: {prompt}
Title: {title}
Type: {slide_type}

CONTEXT:
{context}

TARGET AUDIENCE: {audience['focus']}
Key concerns: {audience['key_concerns']}
Detail level: {audience['detail_level']}

TONE: {tone['vocabulary']}, {tone['style']}

RHETORICAL STRUCTURE: {structure['description']}
Flow: {', '.join(structure['flow'])}
""",
    ]
    
    # Add numerical data if available for data-to-text generation
    if numerical_data:
        prompt_parts.append(f"""
NUMERICAL DATA (generate natural language insights):
{json.dumps(numerical_data, indent=2)}
""")
    
    # Complete prompt with output format
    prompt_parts.append("""Create JSON with:
- heading: main heading (engaging and clear)
- body_text: 2-4 sentences of compelling content
- bullet_points: 3-5 key bullet points as array
- callout: optional compelling quote or statistic
- data_insight: (optional) natural language insight from numerical data

Output only JSON.""")
    
    return "".join(prompt_parts)
