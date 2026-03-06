"""
Banana Slides CLI - AI-powered PPT generation from command line

Usage:
    banana-slides generate-outline --idea "Your presentation idea"
    banana-slides generate-descriptions --outline outline.json
    banana-slides generate-images --descriptions descriptions.json --output ./slides
    banana-slides export-pptx --images ./slides --output presentation.pptx
    banana-slides export-pdf --images ./slides --output presentation.pdf
    
    # Full pipeline
    banana-slides create --idea "Your presentation idea" --output presentation.pptx
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict

import click
from dotenv import load_dotenv

# Setup path
_project_root = Path(__file__).parent.parent
_env_file = _project_root / '.env'
load_dotenv(dotenv_path=_env_file, override=True)

# Add backend to path
sys.path.insert(0, str(_project_root / 'backend'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== Configuration ====================

class CLIConfig:
    """CLI Configuration - reads from environment variables"""
    
    AI_PROVIDER_FORMAT = os.getenv('AI_PROVIDER_FORMAT', 'gemini')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GOOGLE_API_BASE = os.getenv('GOOGLE_API_BASE', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    TEXT_MODEL = os.getenv('TEXT_MODEL', 'gemini-2.0-flash-exp')
    IMAGE_MODEL = os.getenv('IMAGE_MODEL', 'gemini-2.0-flash-exp')
    IMAGE_CAPTION_MODEL = os.getenv('IMAGE_CAPTION_MODEL', 'gemini-2.0-flash-exp')
    DEFAULT_ASPECT_RATIO = os.getenv('DEFAULT_ASPECT_RATIO', '16:9')
    DEFAULT_RESOLUTION = os.getenv('DEFAULT_RESOLUTION', '2K')
    OUTPUT_LANGUAGE = os.getenv('OUTPUT_LANGUAGE', 'en')
    MAX_DESCRIPTION_WORKERS = int(os.getenv('MAX_DESCRIPTION_WORKERS', '5'))
    MAX_IMAGE_WORKERS = int(os.getenv('MAX_IMAGE_WORKERS', '8'))


def _get_ai_service():
    """Get AI service instance."""
    from backend.services.ai_service_manager import get_ai_service
    return get_ai_service()


def _flatten_outline(outline: List[Dict]) -> List[Dict]:
    """Flatten outline with parts into a simple list of pages."""
    from backend.services.ai_service import AIService
    return AIService.flatten_outline(outline)


# ==================== CLI Commands ====================

@click.group()
@click.version_option(version='0.4.0')
def cli():
    """Banana Slides CLI - AI-powered PPT generation from command line"""
    pass


@cli.command('generate-outline')
@click.option('--idea', '-i', required=True, help='Presentation idea or topic')
@click.option('--output', '-o', default='outline.json', help='Output JSON file')
@click.option('--language', '-l', default=None, help='Output language (zh, ja, en, auto)')
def generate_outline(idea: str, output: str, language: Optional[str]):
    """Generate presentation outline from an idea."""
    from backend.services.ai_service import ProjectContext
    
    click.echo(f"Generating outline from: {idea}")
    
    try:
        ai_service = _get_ai_service()
        output_lang = language or CLIConfig.OUTPUT_LANGUAGE
        context = ProjectContext({'idea_prompt': idea, 'creation_type': 'idea'})
        
        click.echo("AI is thinking...")
        outline = ai_service.generate_outline(project_context=context, language=output_lang)
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)
        
        flat_pages = _flatten_outline(outline)
        click.echo(f"Done! Generated {len(flat_pages)} slides in {len(outline)} sections -> {output}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command('generate-descriptions')
@click.option('--outline', '-i', 'outline_file', required=True, 
              type=click.Path(exists=True), help='Input outline JSON file')
@click.option('--output', '-o', default='descriptions.json', help='Output JSON file')
@click.option('--idea', '-idea', default=None, help='Original idea (for context)')
@click.option('--language', '-l', default=None, help='Output language (zh, ja, en, auto)')
def generate_descriptions(outline_file: str, output: str, idea: Optional[str], 
                         language: Optional[str]):
    """Generate detailed page descriptions from outline."""
    from backend.services.ai_service import ProjectContext
    
    with open(outline_file, 'r', encoding='utf-8') as f:
        outline = json.load(f)
    
    click.echo(f"Loading outline from: {outline_file}")
    
    try:
        ai_service = _get_ai_service()
        output_lang = language or CLIConfig.OUTPUT_LANGUAGE
        context = ProjectContext({'idea_prompt': idea or 'Presentation', 'creation_type': 'idea'})
        
        click.echo("Generating descriptions...")
        flat_pages = _flatten_outline(outline)
        
        descriptions = []
        for page_idx, page_outline in enumerate(flat_pages):
            click.echo(f"  Page {page_idx + 1}/{len(flat_pages)}: {page_outline.get('title', 'Untitled')}")
            
            desc_result = ai_service.generate_page_description(
                project_context=context,
                outline=outline,
                page_outline=page_outline,
                page_index=page_idx + 1,
                language=output_lang
            )
            
            descriptions.append({
                'page_index': page_idx,
                'outline': page_outline,
                'description': desc_result.get('text', ''),
                'extra_fields': desc_result.get('extra_fields', {})
            })
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=2)
        
        click.echo(f"Done! Generated {len(descriptions)} descriptions -> {output}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command('generate-images')
@click.option('--descriptions', '-i', 'descriptions_file', required=True,
              type=click.Path(exists=True), help='Input descriptions JSON file')
@click.option('--output', '-o', default='./slides', help='Output directory')
@click.option('--aspect-ratio', '-r', default=None, help='Image aspect ratio (16:9, 4:3)')
@click.option('--resolution', '-res', default=None, help='Image resolution (1K, 2K, 4K)')
def generate_images(descriptions_file: str, output: str, aspect_ratio: Optional[str],
                   resolution: Optional[str]):
    """Generate slide images from descriptions."""
    from backend.services.file_service import FileService
    import shutil
    
    with open(descriptions_file, 'r', encoding='utf-8') as f:
        descriptions = json.load(f)
    
    click.echo(f"Loading {len(descriptions)} descriptions from: {descriptions_file}")
    
    try:
        ai_service = _get_ai_service()
        img_aspect_ratio = aspect_ratio or CLIConfig.DEFAULT_ASPECT_RATIO
        img_resolution = resolution or CLIConfig.DEFAULT_RESOLUTION
        
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"Generating images (aspect: {img_aspect_ratio}, resolution: {img_resolution})...")
        
        file_service = FileService(base_dir=str(_project_root / 'output'))
        
        generated_files = []
        for page_idx, desc in enumerate(descriptions):
            page_outline = desc.get('outline', {})
            title = page_outline.get('title', f'Slide {page_idx + 1}')
            description_text = desc.get('description', '')
            
            click.echo(f"  Page {page_idx + 1}/{len(descriptions)}: {title}")
            
            image_path = ai_service.generate_image(
                prompt=description_text,
                ref_image_path=None,
                project_id='cli-project',
                page_index=page_idx,
                file_service=file_service,
                aspect_ratio=img_aspect_ratio,
                resolution=img_resolution
            )
            
            if image_path and os.path.exists(image_path):
                dst = output_dir / f"slide_{page_idx + 1:02d}.png"
                shutil.copy2(image_path, dst)
                generated_files.append(str(dst))
                click.echo(f"    Generated: {dst.name}")
            else:
                click.echo(f"    Failed")
        
        click.echo(f"Done! Generated {len(generated_files)} images -> {output}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command('export-pptx')
@click.option('--images', '-i', 'images_dir', required=True,
              type=click.Path(exists=True), help='Directory with slide images')
@click.option('--output', '-o', default='presentation.pptx', help='Output PPTX file')
@click.option('--aspect-ratio', '-r', default='16:9', help='Image aspect ratio')
def export_pptx(images_dir: str, output: str, aspect_ratio: str):
    """Export slide images to PPTX file."""
    from backend.services.export_service import ExportService
    from pathlib import Path
    
    images_path = Path(images_dir)
    
    image_files = (sorted([str(f) for f in images_path.glob('*.png')]) + 
                  sorted([str(f) for f in images_path.glob('*.jpg')]) + 
                  sorted([str(f) for f in images_path.glob('*.jpeg')]))
    
    if not image_files:
        click.echo(f"No images found in: {images_dir}", err=True)
        sys.exit(1)
    
    click.echo(f"Found {len(image_files)} images in: {images_dir}")
    
    try:
        export_service = ExportService()
        export_service.create_pptx_from_images(
            image_paths=image_files,
            output_file=output,
            aspect_ratio=aspect_ratio
        )
        click.echo(f"Done! PPTX saved -> {output}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command('export-pdf')
@click.option('--images', '-i', 'images_dir', required=True,
              type=click.Path(exists=True), help='Directory with slide images')
@click.option('--output', '-o', default='presentation.pdf', help='Output PDF file')
@click.option('--aspect-ratio', '-r', default='16:9', help='Image aspect ratio')
def export_pdf(images_dir: str, output: str, aspect_ratio: str):
    """Export slide images to PDF file."""
    from backend.services.export_service import ExportService
    from pathlib import Path
    
    images_path = Path(images_dir)
    
    image_files = (sorted([str(f) for f in images_path.glob('*.png')]) + 
                  sorted([str(f) for f in images_path.glob('*.jpg')]) + 
                  sorted([str(f) for f in images_path.glob('*.jpeg')]))
    
    if not image_files:
        click.echo(f"No images found in: {images_dir}", err=True)
        sys.exit(1)
    
    click.echo(f"Found {len(image_files)} images in: {images_dir}")
    
    try:
        export_service = ExportService()
        export_service.create_pdf_from_images(
            image_paths=image_files,
            output_file=output,
            aspect_ratio=aspect_ratio
        )
        click.echo(f"Done! PDF saved -> {output}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command('create')
@click.option('--idea', '-i', required=True, help='Presentation idea or topic')
@click.option('--output', '-o', default='presentation.pptx', help='Output file')
@click.option('--format', '-f', 'output_format', 
              type=click.Choice(['pptx', 'pdf', 'images']), default='pptx',
              help='Output format')
@click.option('--language', '-l', default=None, help='Output language (zh, ja, en, auto)')
@click.option('--aspect-ratio', '-r', default=None, help='Image aspect ratio (16:9, 4:3)')
@click.option('--resolution', '-res', default=None, help='Image resolution (1K, 2K, 4K)')
def create_presentation(idea: str, output: str, output_format: str,
                        language: Optional[str], aspect_ratio: Optional[str],
                        resolution: Optional[str]):
    """Create a complete presentation in one command."""
    import tempfile
    import shutil
    
    if output.endswith('.pdf'):
        output_format = 'pdf'
    elif output.endswith('.pptx'):
        output_format = 'pptx'
    
    click.echo(f"\n=== Banana Slides CLI ===")
    click.echo(f"Input: {idea}")
    click.echo(f"Output: {output} ({output_format})\n")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        from backend.services.ai_service import ProjectContext
        from backend.services.file_service import FileService
        
        ai_service = _get_ai_service()
        output_lang = language or CLIConfig.OUTPUT_LANGUAGE
        img_aspect_ratio = aspect_ratio or CLIConfig.DEFAULT_ASPECT_RATIO
        img_resolution = resolution or CLIConfig.DEFAULT_RESOLUTION
        
        # Step 1: Generate outline
        click.echo("=== Step 1: Generate Outline ===")
        context = ProjectContext({'idea_prompt': idea, 'creation_type': 'idea'})
        outline = ai_service.generate_outline(project_context=context, language=output_lang)
        flat_pages = _flatten_outline(outline)
        click.echo(f"Generated {len(flat_pages)} slides\n")
        
        # Step 2: Generate descriptions
        click.echo("=== Step 2: Generate Descriptions ===")
        descriptions = []
        for page_idx, page_outline in enumerate(flat_pages):
            click.echo(f"  Page {page_idx + 1}/{len(flat_pages)}")
            desc_result = ai_service.generate_page_description(
                project_context=context, outline=outline, page_outline=page_outline,
                page_index=page_idx + 1, language=output_lang
            )
            descriptions.append({
                'page_index': page_idx,
                'outline': page_outline,
                'description': desc_result.get('text', ''),
                'extra_fields': desc_result.get('extra_fields', {})
            })
        click.echo(f"Generated {len(descriptions)} descriptions\n")
        
        # Step 3: Generate images
        click.echo("=== Step 3: Generate Images ===")
        file_service = FileService(base_dir=str(_project_root / 'output'))
        
        generated_files = []
        for page_idx, desc in enumerate(descriptions):
            page_outline = desc.get('outline', {})
            title = page_outline.get('title', f'Slide {page_idx + 1}')
            description_text = desc.get('description', '')
            
            click.echo(f"  Page {page_idx + 1}/{len(descriptions)}: {title}")
            
            image_path = ai_service.generate_image(
                prompt=description_text, ref_image_path=None, project_id='cli-project',
                page_index=page_idx, file_service=file_service,
                aspect_ratio=img_aspect_ratio, resolution=img_resolution
            )
            
            if image_path and os.path.exists(image_path):
                dst = Path(temp_dir) / f"slide_{page_idx + 1:02d}.png"
                shutil.copy2(image_path, dst)
                generated_files.append(str(dst))
                click.echo(f"    OK")
            else:
                click.echo(f"    FAILED")
        
        click.echo(f"Generated {len(generated_files)} images\n")
        
        # Step 4: Export
        click.echo(f"=== Step 4: Export to {output_format.upper()} ===")
        
        if output_format == 'pptx':
            from backend.services.export_service import ExportService
            export_service = ExportService()
            export_service.create_pptx_from_images(
                image_paths=generated_files, output_file=output, aspect_ratio=img_aspect_ratio
            )
            click.echo(f"Done! PPTX saved -> {output}\n")
        
        elif output_format == 'pdf':
            from backend.services.export_service import ExportService
            export_service = ExportService()
            export_service.create_pdf_from_images(
                image_paths=generated_files, output_file=output, aspect_ratio=img_aspect_ratio
            )
            click.echo(f"Done! PDF saved -> {output}\n")
        
        elif output_format == 'images':
            final_dir = Path(output)
            final_dir.mkdir(parents=True, exist_ok=True)
            for src in generated_files:
                shutil.move(src, final_dir / Path(src).name)
            click.echo(f"Done! Images saved -> {final_dir}\n")
        
        click.echo("Presentation created successfully!")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if output_format != 'images' and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@cli.command('config')
def show_config():
    """Show current configuration."""
    click.echo("=== Banana Slides CLI Configuration ===")
    
    items = [
        ("AI Provider", CLIConfig.AI_PROVIDER_FORMAT),
        ("Text Model", CLIConfig.TEXT_MODEL),
        ("Image Model", CLIConfig.IMAGE_MODEL),
        ("Default Aspect Ratio", CLIConfig.DEFAULT_ASPECT_RATIO),
        ("Default Resolution", CLIConfig.DEFAULT_RESOLUTION),
        ("Output Language", CLIConfig.OUTPUT_LANGUAGE),
    ]
    
    for key, value in items:
        click.echo(f"  {key}: {value}")


if __name__ == '__main__':
    cli()
