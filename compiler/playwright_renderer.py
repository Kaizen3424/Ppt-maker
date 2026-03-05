"""Playwright renderer for visual QA."""
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path


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
    
    # Generate HTML for the slide
    html = _slide_to_html(slide, width, height)
    
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


def _slide_to_html(slide: Dict[str, Any], width: int, height: int) -> str:
    """Convert slide data to HTML for rendering."""
    
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    heading = slide.get("heading", title)
    body_text = slide.get("body_text", "")
    bullets = slide.get("bullet_points", [])
    callout = slide.get("callout", "")
    
    # Calculate scale factor based on slide dimensions
    # Standard slide is 13.333 x 7.5 inches
    # At 96 DPI: 1280 x 720 pixels
    scale_x = width / 13.333
    scale_y = height / 7.5
    
    # Convert layout elements if present
    elements_html = ""
    layout = slide.get("layout", {})
    for elem in layout.get("elements", []):
        elem_type = elem.get("type", "")
        x = elem.get("x", 0) * scale_x
        y = elem.get("y", 0) * scale_y
        w = elem.get("width", 5) * scale_x
        h = elem.get("height", 1) * scale_y
        
        # Get content for this element
        content = ""
        if elem_type == "title" or elem_type == "heading":
            content = heading
        elif elem_type == "subtitle" or elem_type == "subheading":
            content = slide.get("subheading", "")
        elif elem_type == "body":
            content = body_text
        elif elem_type == "bullets":
            content = "<br>".join([f"• {b}" for b in bullets])
        
        if content:
            elements_html += f'''
            <div style="
                position: absolute;
                left: {x}px;
                top: {y}px;
                width: {w}px;
                height: {h}px;
                font-size: {16 if elem_type in ['title', 'heading'] else 14}px;
                overflow: hidden;
                word-wrap: break-word;
            ">{content}</div>'''
    
    # If no layout elements, use default rendering
    if not elements_html:
        elements_html = f'''
        <h1 style="position: absolute; left: 50px; top: 50px; width: {width-100}px;">{heading}</h1>
        <p style="position: absolute; left: 50px; top: 150px; width: {width-100}px;">{body_text}</p>
        <ul style="position: absolute; left: 50px; top: 300px; width: {width-100}px;">
            {"".join([f"<li>{b}</li>" for b in bullets])}
        </ul>'''
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: {width}px;
            height: {height}px;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            overflow: hidden;
        }}
        h1 {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        p {{
            font-size: 18px;
            line-height: 1.6;
        }}
        ul {{
            font-size: 18px;
            line-height: 1.8;
            padding-left: 30px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .title-slide {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            text-align: center;
        }}
    </style>
</head>
<body>
    {elements_html}
</body>
</html>'''
    
    return html


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
