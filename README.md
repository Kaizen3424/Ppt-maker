# AI Presentation CLI

A multi-agent AI system that automatically generates PowerPoint presentations. Just provide a topic, and the system researches, writes content, designs layouts, and creates a professional `.pptx` file.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

## Features

- 🤖 **5 AI Agents** - Orchestrator, Researcher, Narrative, Designer, Visual QA
- 🔍 **Web Research** - Real-time information via Tavily API
- 📊 **Smart Content** - LLM-powered slide content generation
- 📐 **Visual Layouts** - Automatic spatial design for each slide
- 📄 **PPTX Output** - Native PowerPoint file generation
- 🎨 **Beautiful CLI** - Rich terminal interface with progress indicators

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API keys in config.yaml

# Generate a presentation
python cli.py generate "AI in Healthcare" --output ai_healthcare.pptx
```

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Kaizen3424/Ppt-maker.git
cd Ppt-maker
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Edit `config.yaml`:
```yaml
# LLM Proxy
llm_proxy:
  base_url: "https://your-proxy-url/v1"
  api_key: "your-api-key"

# Tavily Search (optional)
tavily:
  api_key: "your-tavily-key"

# Model routing
llm_routing:
  orchestrator_agent:
    model: "moonshotai/kimi-k2-instruct-0905"
```

## Usage

### Basic Command
```bash
python cli.py generate "Your Topic" --output presentation.pptx
```

### Examples
```bash
# AI presentation
python cli.py generate "Artificial Intelligence in Education" --output ai_edu.pptx

# Business presentation
python cli.py generate "Q4 Marketing Strategy" --output q4_marketing.pptx

# Science presentation
python cli.py generate "Climate Change Impact on Oceans" --output oceans.pptx
```

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `llm_proxy.base_url` | LLM API endpoint | Required |
| `llm_proxy.api_key` | LLM API key | Required |
| `tavily.api_key` | Tavily search API key | Optional |
| `search.tavily.max_results` | Search results per query | 5 |

### Supported Models

The CLI works with any OpenAI-compatible API. Examples:
- `moonshotai/kimi-k2-instruct-0905`
- `gpt-4o`
- `claude-3-sonnet`
- `gemini-pro`

## How It Works

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Orchestrator│ -> │ Researcher  │ -> │ Narrative   │
│ Plan slides │    │ Web search  │    │ Write content│
└─────────────┘    └─────────────┘    └─────────────┘
                                                │
┌─────────────┐    ┌─────────────┐             │
│ Visual QA   │ <- │ Designer    │ <───────────┘
│ Check quality│   │ Calc layouts│
└─────────────┘    └─────────────┘
                          │
                          v
                   ┌─────────────┐
                   │    PPTX     │
                   │  Generator  │
                   └─────────────┘
```

## Project Structure

```
ai-presentation-cli/
├── agents/           # AI agent implementations
│   ├── orchestrator.py
│   ├── researcher.py
│   ├── narrative.py
│   ├── designer.py
│   └── visual_qa.py
├── compiler/         # Output generators
│   ├── pptx_builder.py
│   └── playwright_renderer.py
├── core/            # Core utilities
│   ├── config.py
│   ├── llm.py
│   └── state.py
├── tools/           # External tools
│   └── search.py
├── graph.py         # LangGraph pipeline
├── cli.py           # CLI interface
├── config.yaml      # Configuration
└── requirements.txt # Dependencies
```

## Development

### Running Tests
```bash
# Test single component
python -c "from compiler.pptx_builder import generate_pptx; print('OK')"

# Test full pipeline
python -c "
from graph import build_graph
graph = build_graph()
result = graph.invoke({'prompt': 'Test', 'metadata': {}, 'json_deck': {'slides': []}, 'errors': [], 'current_agent': 'Start'})
print(f'Slides: {len(result[\"json_deck\"][\"slides\"])}')
"
```

### Adding New Agents

1. Create `agents/new_agent.py`
2. Register in `agents/__init__.py`
3. Add to pipeline in `graph.py`

## Troubleshooting

**No module named 'pptx'**
```bash
pip install python-pptx
```

**Tavily API error**
- Add your API key to `config.yaml`
- Or set: `export TAVILY_API_KEY=your-key`

**Empty PPTX file**
- Check python-pptx is installed: `pip install -U python-pptx`

## License

MIT License - See [LICENSE](LICENSE) for details.

---

For detailed developer documentation, see [progress.md](progress.md).
