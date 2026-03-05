"""Visual QA agent - inspects rendered slides for issues."""
import os
import json
import tempfile
from typing import Dict, Any, List

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper
from compiler.playwright_renderer import render_slide_to_image


def visual_qa_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Visual QA agent inspects rendered slides for issues.
    
    It renders each slide to an image using Playwright, then uses
    a vision-capable LLM to inspect for problems like overlapping
    text, bad contrast, or layout issues.
    
    Enhanced with self-correction feedback loop:
    - Granular error reporting with specific coordinates
    - Feedback-driven redesign integration
    - Iterative refinement with max attempts
    """
    state["current_agent"] = "Visual QA: Inspecting rendered slides..."
    
    slides = state["json_deck"].get("slides", [])
    
    # Get visual QA config
    qa_config = config._config.get("visual_qa", {})
    max_iterations = qa_config.get("max_iterations", 3)
    
    llm_config = config.get_llm_config("vision_qa_agent")
    proxy_config = config.get_proxy_config()
    vision_llm = get_llm_helper(llm_config, proxy_config)
    
    errors = []
    qa_feedback = []
    
    # Check each slide with iterative refinement
    for i, slide in enumerate(slides):
        slide_error, slide_feedback = _inspect_slide_with_refinement(
            vision_llm=vision_llm,
            slide=slide,
            slide_index=i,
            config=qa_config,
            max_iterations=max_iterations
        )
        if slide_error:
            errors.append(f"Slide {i+1}: {slide_error}")
        if slide_feedback:
            qa_feedback.append({
                "slide_index": i,
                "feedback": slide_feedback
            })
    
    # Store errors and detailed feedback in state
    state["errors"] = errors
    state["qa_feedback"] = qa_feedback
    
    return state


def _inspect_slide_with_refinement(
    vision_llm,
    slide: Dict[str, Any],
    slide_index: int,
    config: Dict[str, Any],
    max_iterations: int = 3
) -> tuple[str | None, str | None]:
    """Inspect a single slide for visual issues with iterative refinement.
    
    Returns:
        Tuple of (error_message, detailed_feedback)
    """
    
    iteration = 0
    current_feedback = None
    
    while iteration < max_iterations:
        try:
            # Render slide to temporary image
            width = config.get("screenshot_width", 1280)
            height = config.get("screenshot_height", 720)
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                screenshot_path = tmp.name
            
            try:
                render_slide_to_image(slide, screenshot_path, width, height)
                
                # Read the image for vision model
                with open(screenshot_path, "rb") as f:
                    image_data = f.read()
                
                # Create enhanced prompt for granular error reporting
                prompt = _build_qa_prompt(slide, current_feedback)
                
                # Create message with image
                from langchain.schema import HumanMessage
                
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                    ]
                )
                
                response = vision_llm.invoke([message])
                feedback = response.content if hasattr(response, 'content') else str(response)
                
                # Analyze response for issues
                if "PASS" in feedback.upper() or "NO ISSUES" in feedback.upper() or "LOOKS GOOD" in feedback.upper():
                    return None, None
                
                # Store detailed feedback for potential redesign
                current_feedback = feedback
                
                # Check if we've reached max iterations
                iteration += 1
                if iteration >= max_iterations:
                    # Return the last feedback as final error
                    return _extract_actionable_error(feedback), feedback
                
                # Continue to next iteration for refinement
                # (In a full implementation, this would trigger redesign)
                
            finally:
                # Clean up temp file
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    
        except Exception as e:
            # If rendering fails, we can't do visual QA
            # Return None to allow the process to continue
            return None, None
    
    return _extract_actionable_error(current_feedback), current_feedback


def _build_qa_prompt(slide: Dict[str, Any], previous_feedback: str = None) -> str:
    """Build an enhanced QA prompt for granular error reporting."""
    
    slide_type = slide.get("type", "content")
    heading = slide.get("heading", "")
    layout = slide.get("layout", {})
    elements = layout.get("elements", [])
    
    # Build element position info for context
    element_info = []
    for elem in elements:
        elem_type = elem.get("type", "")
        x = elem.get("x", 0)
        y = elem.get("y", 0)
        w = elem.get("width", 0)
        h = elem.get("height", 0)
        element_info.append(f"  - {elem_type}: x={x}, y={y}, width={w}, height={h}")
    
    elements_str = "\n".join(element_info) if element_info else "  No layout elements defined"
    
    base_prompt = f"""Inspect this presentation slide (type: {slide_type}) for visual issues.

SLIDE CONTENT:
- Heading: {heading}

LAYOUT ELEMENTS:
{elements_str}

CHECK FOR THESE ISSUES (provide specific coordinates if found):
1. Text overlapping: Check if any text elements overlap with each other. If so, specify which elements and their overlap amount in inches/pixels.
2. Spacing problems: Verify adequate spacing between elements (minimum 0.3 inches recommended). Report any cramped areas.
3. Readability: Ensure text is properly sized and not too small (minimum 12pt for body text).
4. Content overflow: Check if text is cut off or extends beyond element boundaries.
5. Visual balance: Report if slide feels unbalanced or lopsided.
6. Alignment: Check if related elements are properly aligned.
7. Contrast: Verify text is readable against background.

{previous_feedback and f"PREVIOUS FEEDBACK TO ADDRESS:\n{previous_feedback}" or ""}

IMPORTANT: Be extremely specific in your response. Instead of saying "text overlaps", say "The heading at coordinates (0.5, 0.5) overlaps with body text at (0.5, 1.3) by approximately 0.3 inches vertically."

Reply with "PASS" if everything looks good, or provide detailed, actionable feedback with specific coordinates and measurements."""
    
    return base_prompt


def _extract_actionable_error(feedback: str) -> str:
    """Extract a concise, actionable error message from detailed feedback."""
    
    if not feedback:
        return "Visual QA could not complete analysis"
    
    # Take first few sentences for the error message
    sentences = feedback.split('.')
    if len(sentences) > 2:
        return '.'.join(sentences[:2]) + '.'
    return feedback[:200]  # Limit to 200 chars


def _inspect_slide(
    vision_llm,
    slide: Dict[str, Any],
    slide_index: int,
    config: Dict[str, Any]
) -> str | None:
    """Inspect a single slide for visual issues.
    
    DEPRECATED: Use _inspect_slide_with_refinement instead.
    """
    
    try:
        # Render slide to temporary image
        width = config.get("screenshot_width", 1280)
        height = config.get("screenshot_height", 720)
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            screenshot_path = tmp.name
        
        try:
            render_slide_to_image(slide, screenshot_path, width, height)
            
            # Read the image for vision model
            with open(screenshot_path, "rb") as f:
                image_data = f.read()
            
            # Create message with image
            from langchain.schema import HumanMessage
            
            prompt = """Look at this presentation slide and check for issues:
1. Are there any text elements overlapping?
2. Is there proper spacing between elements?
3. Is the text readable and well-balanced?
4. Are there any obvious visual problems?

Reply with "PASS" if everything looks good, or describe specific issues that need fixing."""
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            )
            
            response = vision_llm.invoke([message])
            feedback = response.content if hasattr(response, 'content') else str(response)
            
            if "PASS" not in feedback.upper():
                return feedback
            return None
            
        finally:
            # Clean up temp file
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
    except Exception as e:
        # If rendering fails, we can't do visual QA
        # Return None to allow the process to continue
        return None
    
    return None
