"""Playwright renderer for visual QA with enhanced HTML/CSS fidelity."""
import os
import json
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path


# Theme configurations for CSS mapping
THEME_CSS_MAP = {
    "default": {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "text": "#ffffff",
        "title_font": "Arial, sans-serif",
        "body_font": "Arial, sans-serif",
        "title_size": "44px",
        "heading_size": "32px",
        "body_size": "18px",
        "bullet_size": "16px"
    },
    "corporate": {
        "primary": "#003366",
        "secondary": "#336699",
        "text": "#ffffff",
        "title_font": "Calibri, sans-serif",
        "body_font": "Calibri, sans-serif",
        "title_size": "40px",
        "heading_size": "28px",
        "body_size": "16px",
        "bullet_size": "14px"
    },
    "modern": {
        "primary": "#ff5733",
        "secondary": "#ff9900",
        "text": "#ffffff",
        "title_font": "Segoe UI, sans-serif",
        "body_font": "Segoe UI, sans-serif",
        "title_size": "48px",
        "heading_size": "36px",
        "body_size": "20px",
        "bullet_size": "18px"
    },
    "minimal": {
        "primary": "#212121",
        "secondary": "#424242",
        "text": "#000000",
        "title_font": "Helvetica, Arial, sans-serif",
        "body_font": "Helvetica, Arial, sans-serif",
        "title_size": "42px",
        "heading_size": "30px",
        "body_size": "18px",
        "bullet_size": "16px"
    }
}


def render_slide_to_image(
    slide: Dict[str, Any],
    output_path: str,
    width: int = 1280,
    height: int = 720
) -> str:
    """Render a slide to an image using Playwright.
    
    Args:
        slide: The slide data dictionary
        output_path: Path where the screenshot will be saved
        width: Screenshot width in pixels
        height: Screenshot height in pixels
        
    Returns:
        Path to the saved screenshot
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Fallback: create a placeholder image if Playwright not available
        return _create_placeholder_image(slide, output_path, width, height)
    
    # Generate enhanced HTML for the slide
    html = _slide_to_enhanced_html(slide, width, height)
    
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html)
        html_path = f.name
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            
            # Load the HTML file
            page.goto(f"file://{html_path}")
            
            # Wait for rendering
            page.wait_for_timeout(500)
            
            # Take screenshot
            page.screenshot(path=output_path, full_page=False)
            
            browser.close()
    finally:
        # Clean up temp HTML file
        if os.path.exists(html_path):
            os.remove(html_path)
    
    return output_path


def _create_placeholder_image(
    slide: Dict[str, Any],
    output_path: str,
    width: int,
    height: int
) -> str:
    """Create a placeholder image when Playwright is not available."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple colored background
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw title
        title = slide.get("title", "Slide")
        draw.text((50, 50), title, fill=(0, 0, 0))
        
        # Draw content preview
        body = slide.get("body_text", "")[:100]
        if body:
            draw.text((50, 150), body, fill=(80, 80, 80))
        
        img.save(output_path)
    except ImportError:
        # If PIL not available either, create empty file
        with open(output_path, "wb") as f:
            f.write(b"")
    
    return output_path


def _slide_to_enhanced_html(slide: Dict[str, Any], width: int, height: int) -> str:
    """Convert slide data to enhanced HTML with advanced CSS styling."""
    
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    heading = slide.get("heading", title)
    body_text = slide.get("body_text", "")
    bullets = slide.get("bullet_points", [])
    callout = slide.get("callout", "")
    subheading = slide.get("subheading", "")
    
    # Get layout and theme information
    layout = slide.get("layout", {})
    theme_config = layout.get("theme", {})
    background = layout.get("background", {})
    
    # Determine theme
    theme_name = theme_config.get("color_scheme", "default")
    theme = THEME_CSS_MAP.get(theme_name, THEME_CSS_MAP["default"])
    
    # Calculate scale factor based on slide dimensions
    # Standard slide is 13.333 x 7.5 inches
    # At 96 DPI: 1280 x 720 pixels
    scale_x = width / 13.333
    scale_y = height / 7.5
    
    # Generate enhanced elements HTML
    elements_html = _generate_layout_elements_html(
        slide=slide,
        layout=layout,
        scale_x=scale_x,
        scale_y=scale_y,
        theme=theme
    )
    
    # If no layout elements, use default rendering
    if not elements_html:
        elements_html = _generate_default_html(heading, body_text, bullets, theme)
    
    # Build enhanced CSS with theme support
    background_css = _build_background_css(background, theme)
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            width: {width}px;
            height: {height}px;
            overflow: hidden;
            font-family: {theme["body_font"]};
            {background_css}
        }}
        
        .slide-container {{
            position: relative;
            width: 100%;
            height: 100%;
        }}
        
        /* Title styles */
        .title, .heading {{
            font-size: {theme["title_size"]};
            font-weight: bold;
            color: {theme["text"]};
            margin-bottom: 0.5em;
        }}
        
        /* Subtitle styles */
        .subtitle, .subheading {{
            font-size: {theme["heading_size"]};
            font-weight: normal;
            color: {theme["text"]};
            opacity: 0.9;
        }}
        
        /* Body text styles */
        .body, .body-text {{
            font-size: {theme["body_size"]};
            line-height: 1.6;
            color: {theme["text"]};
        }}
        
        /* Bullet styles */
        .bullets, ul {{
            font-size: {theme["bullet_size"]};
            line-height: 1.8;
            color: {theme["text"]};
            padding-left: 30px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        /* Callout/quote styles */
        .callout {{
            font-size: 14px;
            font-style: italic;
            color: {theme["text"]};
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-left: 4px solid {theme["secondary"]};
        }}
        
        /* Element positioning */
        .element {{
            position: absolute;
            overflow: hidden;
            word-wrap: break-word;
        }}
        
        /* Alignment classes */
        .align-left {{ text-align: left; }}
        .align-center {{ text-align: center; }}
        .align-right {{ text-align: right; }}
        
        /* Bold text */
        .weight-bold {{ font-weight: bold; }}
        .weight-normal {{ font-weight: normal; }}
        
        /* CTA styles */
        .cta {{
            font-size: 20px;
            color: {theme["text"]};
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="slide-container">
        {elements_html}
    </div>
</body>
</html>'''
    
    return html


def _generate_layout_elements_html(
    slide: Dict[str, Any],
    layout: Dict[str, Any],
    scale_x: float,
    scale_y: float,
    theme: Dict[str, Any]
) -> str:
    """Generate HTML for layout elements with precise positioning."""
    
    elements = layout.get("elements", [])
    if not elements:
        return ""
    
    heading = slide.get("heading", "")
    body_text = slide.get("body_text", "")
    bullets = slide.get("bullet_points", [])
    callout = slide.get("callout", "")
    subheading = slide.get("subheading", "")
    
    html_parts = []
    
    for elem in elements:
        elem_type = elem.get("type", "")
        x = elem.get("x", 0) * scale_x
        y = elem.get("y", 0) * scale_y
        w = elem.get("width", 5) * scale_x
        h = elem.get("height", 1) * scale_y
        style = elem.get("style", {})
        
        # Get alignment
        alignment = style.get("alignment", "left")
        weight = style.get("weight", "normal")
        
        # Build CSS classes
        css_classes = ["element"]
        if elem_type in ["title", "heading"]:
            css_classes.append("title" if elem_type == "title" else "heading")
        elif elem_type in ["subtitle", "subheading"]:
            css_classes.append("subtitle")
        elif elem_type == "body":
            css_classes.append("body")
        elif elem_type == "bullets":
            css_classes.append("bullets")
        elif elem_type == "callout":
            css_classes.append("callout")
        
        # Alignment
        if alignment == "center":
            css_classes.append("align-center")
        elif alignment == "right":
            css_classes.append("align-right")
        
        # Weight
        if weight == "bold":
            css_classes.append("weight-bold")
        
        # Get content for this element
        content = ""
        if elem_type in ["title", "heading"]:
            content = heading
        elif elem_type in ["subtitle", "subheading"]:
            content = subheading
        elif elem_type == "body":
            content = body_text
        elif elem_type == "bullets":
            content = "<ul>" + "".join([f"<li>{b}</li>" for b in bullets]) + "</ul>"
        elif elem_type == "callout":
            content = f'"{callout}"'
        
        if content:
            css_style = f'left: {x}px; top: {y}px; width: {w}px; height: {h}px;'
            html_parts.append(f'<div class="{" ".join(css_classes)}" style="{css_style}">{content}</div>')
    
    return "\n".join(html_parts)


def _generate_default_html(heading: str, body_text: str, bullets: list, theme: Dict[str, Any]) -> str:
    """Generate default HTML when no layout is specified."""
    
    return f'''
    <h1 class="title" style="position: absolute; left: {48*1.2}px; top: {48*1.2}px; width: {1280-96}px; font-size: {theme['title_size']};">{heading}</h1>
    <p class="body" style="position: absolute; left: {48*1.2}px; top: {150}px; width: {1280-96}px; font-size: {theme['body_size']};">{body_text}</p>
    <ul class="bullets" style="position: absolute; left: {48*1.2}px; top: {300}px; width: {1280-96}px; font-size: {theme['bullet_size']};">
        {"".join([f"<li>{b}</li>" for b in bullets])}
    </ul>'''


def _build_background_css(background: Dict[str, Any], theme: Dict[str, Any]) -> str:
    """Build CSS for background based on theme and background config."""
    
    bg_type = background.get("type", "")
    
    if bg_type == "gradient":
        colors = background.get("colors", [theme["primary"], theme["secondary"]])
        if len(colors) == 1:
            colors.append(theme["secondary"])
        return f"background: linear-gradient(135deg, {colors[0]} 0%, {colors[1]} 100%);"
    elif bg_type == "solid":
        color = background.get("color", theme["primary"])
        return f"background: {color};"
    else:
        # Default gradient
        return f"background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);"


def render_deck_to_images(
    json_deck: Dict[str, Any],
    output_dir: str,
    width: int = 1280,
    height: int = 720
) -> list[str]:
    """Render all slides in a deck to images.
    
    Args:
        json_deck: The deck data with slides
        output_dir: Directory to save screenshots
        width: Screenshot width
        height: Screenshot height
        
    Returns:
        List of paths to saved screenshots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    slides = json_deck.get("slides", [])
    paths = []
    
    for i, slide in enumerate(slides):
        output_path = os.path.join(output_dir, f"slide_{i+1:03d}.png")
        render_slide_to_image(slide, output_path, width, height)
        paths.append(output_path)
    
    return paths


# Legacy function for backward compatibility
def _slide_to_html(slide: Dict[str, Any], width: int, height: int) -> str:
    """Convert slide data to HTML for rendering.
    
    DEPRECATED: Use _slide_to_enhanced_html instead.
    """
    return _slide_to_enhanced_html(slide, width, height)
