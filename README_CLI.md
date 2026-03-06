# Banana Slides CLI

AI-powered PPT generation from the command line.

## Features

- Generate presentation outlines from ideas
- Create detailed page descriptions
- Generate slide images using AI
- Export to PPTX or PDF format
- Full pipeline in one command

## Setup

1. **Clone the repository**
```bash
git clone https://github.com/Kaizen3424/Ppt-maker.git
cd Ppt-maker
```

2. **Install dependencies**
```bash
pip install -e .
```

3. **Configure API keys**

Copy `.env.example` to `.env` and add your API key:
```bash
cp .env.example .env
```

Edit `.env` with your AI provider settings:

```env
# AI Provider (gemini, openai, or lazyllm)
AI_PROVIDER_FORMAT=gemini

# Gemini API (default)
GOOGLE_API_KEY=your-api-key-here
GOOGLE_API_BASE=https://generativelanguage.googleapis.com

# Or OpenAI API
# AI_PROVIDER_FORMAT=openai
# OPENAI_API_KEY=your-api-key-here
# OPENAI_API_BASE=https://api.openai.com/v1
```

## Usage

### Quick Start - Full Pipeline

Generate a complete presentation in one command:

```bash
banana-slides create --idea "Your presentation topic" --output presentation.pptx
```

### Step by Step

**1. Generate outline from an idea**
```bash
banana-slides generate-outline --idea "Introduction to Machine Learning" -o outline.json
```

**2. Generate page descriptions**
```bash
banana-slides generate-descriptions --outline outline.json -o descriptions.json
```

**3. Generate slide images**
```bash
banana-slides generate-images --descriptions descriptions.json -o ./slides
```

**4. Export to PPTX**
```bash
banana-slides export-pptx --images ./slides -o presentation.pptx
```

**Or export to PDF**
```bash
banana-slides export-pdf --images ./slides -o presentation.pdf
```

## Options

### generate-outline
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--idea` | `-i` | (required) | Presentation topic/idea |
| `--output` | `-o` | outline.json | Output JSON file |
| `--language` | `-l` | en | Output language (zh, ja, en, auto) |

### generate-descriptions
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--outline` | `-i` | (required) | Input outline JSON file |
| `--output` | `-o` | descriptions.json | Output JSON file |
| `--idea` | | None | Original idea (for context) |
| `--language` | `-l` | en | Output language |

### generate-images
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--descriptions` | `-i` | (required) | Input descriptions JSON file |
| `--output` | `-o` | ./slides | Output directory |
| `--aspect-ratio` | `-r` | 16:9 | Image aspect ratio (16:9, 4:3) |
| `--resolution` | `-res` | 2K | Image resolution (1K, 2K, 4K) |

### export-pptx / export-pdf
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--images` | `-i` | (required) | Directory with slide images |
| `--output` | `-o` | presentation.pptx/pdf | Output file |
| `--aspect-ratio` | `-r` | 16:9 | Image aspect ratio |

### create
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--idea` | `-i` | (required) | Presentation topic/idea |
| `--output` | `-o` | presentation.pptx | Output file |
| `--format` | `-f` | pptx | Output format (pptx, pdf, images) |
| `--language` | `-l` | en | Output language |
| `--aspect-ratio` | `-r` | 16:9 | Image aspect ratio |
| `--resolution` | `-res` | 2K | Image resolution |

## Examples

### English Presentation
```bash
banana-slides create --idea "The History of Artificial Intelligence" --output ai_history.pptx
```

### Chinese Presentation
```bash
banana-slides create --idea "人工智能的未来" --language zh -o ai_future.pptx
```

### Generate Only Images
```bash
banana-slides create --idea "Quarterly Report" --format images --output ./q4_slides
```

### Custom Aspect Ratio
```bash
banana-slides create --idea "Presentation" --aspect-ratio 4:3 --output presentation.pptx
```

### High Resolution
```bash
banana-slides create --idea "Presentation" --resolution 4K --output presentation.pptx
```

## Configuration

Show current configuration:
```bash
banana-slides config
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER_FORMAT` | gemini | AI provider (gemini, openai, lazyllm) |
| `GOOGLE_API_KEY` | - | Gemini API key |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `TEXT_MODEL` | gemini-2.0-flash-exp | Text generation model |
| `IMAGE_MODEL` | gemini-2.0-flash-exp | Image generation model |
| `DEFAULT_ASPECT_RATIO` | 16:9 | Default aspect ratio |
| `DEFAULT_RESOLUTION` | 2K | Default image resolution |
| `OUTPUT_LANGUAGE` | en | Default output language |

## License

AGPL-3.0 - See LICENSE file for details.
