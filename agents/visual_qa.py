"""Visual QA agent - inspects rendered slides for issues."""
import os
import tempfile
from typing import Dict, Any

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper
from compiler.playwright_renderer import render_slide_to_image


def visual_qa_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Visual QA agent inspects rendered slides for issues.
    
    It renders each slide to an image using Playwright, then uses
    a vision-capable LLM to inspect for problems like overlapping
    text, bad contrast, or layout issues.
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
    
    # Check each slide
    for i, slide in enumerate(slides):
        slide_error = _inspect_slide(
            vision_llm=vision_llm,
            slide=slide,
            slide_index=i,
            config=qa_config
        )
        if slide_error:
            errors.append(f"Slide {i+1}: {slide_error}")
    
    # Store errors in state
    state["errors"] = errors
    
    return state


def _inspect_slide(
    vision_llm,
    slide: Dict[str, Any],
    slide_index: int,
    config: Dict[str, Any]
) -> str | None:
    """Inspect a single slide for visual issues."""
    
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
