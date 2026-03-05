"""PPTX compiler - converts JSON deck to PowerPoint file."""
import os
from typing import Dict, Any, List, Optional

# Import at module level for python-pptx
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


def generate_pptx(json_deck: Dict[str, Any], output_path: str) -> str:
    """Generate a PowerPoint file from JSON deck data.
    
    Args:
        json_deck: The deck data with slides
        output_path: Path where the PPTX will be saved
        
    Returns:
        Path to the generated PPTX file
    """
    if not PPTX_AVAILABLE:
        # Fallback: create a placeholder
        return _create_placeholder_pptx(output_path)
    
    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 ratio
    prs.slide_height = Inches(7.5)
    
    slides = json_deck.get("slides", [])
    
    for slide_data in slides:
        _add_slide(prs, slide_data)
    
    # Save the presentation
    prs.save(output_path)
    return output_path


def _add_slide(prs: 'Presentation', slide_data: Dict[str, Any]) -> None:
    """Add a single slide to the presentation."""
    
    slide_type = slide_data.get("type", "content")
    title = slide_data.get("title", "")
    heading = slide_data.get("heading", title)
    body_text = slide_data.get("body_text", "")
    bullets = slide_data.get("bullet_points", [])
    callout = slide_data.get("callout", "")
    
    # Get layout
    if slide_type == "title":
        layout = prs.slide_layouts[0]  # Title slide layout
        slide = prs.slides.add_slide(layout)
        
        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = heading
        
        # Set subtitle if available
        if len(slide.placeholders) > 1:
            subtitle = slide.placeholders[1]
            subtitle.text = slide_data.get("subheading", body_text)
    else:
        # Content slide
        layout = prs.slide_layouts[1]  # Title and Content
        slide = prs.slides.add_slide(layout)
        
        # Set title
        if slide.shapes.title:
            slide.shapes.title.text = heading
        
        # Get content placeholder
        content_placeholder = None
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == 1:  # Body placeholder
                content_placeholder = shape
                break
        
        if content_placeholder:
            # Add body text
            tf = content_placeholder.text_frame
            tf.clear()
            
            if body_text:
                p = tf.paragraphs[0]
                p.text = body_text
                p.level = 0
            
            # Add bullet points
            for bullet in bullets:
                p = tf.add_paragraph()
                p.text = bullet
                p.level = 0
                p.font.size = Pt(18)
        
        # Add callout if present
        if callout:
            _add_callout_box(slide, callout)


def _add_callout_box(prs_slide, text: str) -> None:
    """Add a callout/quote box to a slide."""
    try:
        from pptx.util import Inches
        
        # Add a text box for the callout
        left = Inches(0.5)
        top = Inches(5.5)
        width = Inches(4)
        height = Inches(1.5)
        
        txBox = prs_slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f'"{text}"'
        p.font.size = Pt(14)
        p.font.italic = True
        
        # Add a border/shape
        shape = prs_slide.shapes.add_shape(
            1,  # msoShapeRectangle
            left, top, width, height
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 240, 240)
        shape.line.color.rgb = RGBColor(200, 200, 200)
        shape.text_frame = tf
    except Exception:
        pass


def _create_placeholder_pptx(output_path: str) -> str:
    """Create a placeholder PPTX file when python-pptx is not available."""
    # Create minimal valid PPTX structure
    # This is a minimal valid PPTX (actually just a placeholder message)
    with open(output_path, "w") as f:
        f.write("PPTX generation requires python-pptx package. Please install it.")
    return output_path


def get_presentation_stats(json_deck: Dict[str, Any]) -> Dict[str, Any]:
    """Get statistics about the presentation."""
    slides = json_deck.get("slides", [])
    
    total_bullets = sum(len(s.get("bullet_points", [])) for s in slides)
    has_calls = any(s.get("callout") for s in slides)
    
    return {
        "slide_count": len(slides),
        "total_bullets": total_bullets,
        "slides_with_calls": sum(1 for s in slides if s.get("callout")),
        "types": list(set(s.get("type", "content") for s in slides))
    }
