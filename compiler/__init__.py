"""Compiler package for AI presentation CLI."""
from .pptx_builder import generate_pptx, get_presentation_stats
from .playwright_renderer import render_slide_to_image, render_deck_to_images

__all__ = [
    "generate_pptx",
    "get_presentation_stats",
    "render_slide_to_image",
    "render_deck_to_images"
]
