# AI Presentation CLI - Developer Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Code Structure](#code-structure)
4. [How It Works](#how-it-works)
5. [Setting Up Development Environment](#setting-up-development-environment)
6. [Configuration](#configuration)
7. [Running the Project](#running-the-project)
8. [Testing](#testing)
9. [Extending the Project](#extending-the-project)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

### Aim
This project is a **multi-agent AI system** that automatically generates PowerPoint presentations. Users provide a topic, and the system:
1. Plans the presentation structure
2. Researches the topic on the web
3. Generates compelling content for each slide
4. Designs visual layouts
5. Compiles everything into a `.pptx` file

### Key Features
- **5 Specialized Agents**: Orchestrator, Researcher, Narrative, Designer, Visual QA
- **LLM Proxy Support**: Works with any OpenAI-compatible API endpoint
- **Web Research**: Uses Tavily API for real-time information
- **PPTX Generation**: Creates native PowerPoint files using python-pptx
- **Rich CLI**: Beautiful terminal UI with progress indicators

---

## Architecture

### Multi-Agent System
The project uses **LangGraph** (by LangChain) to coordinate multiple AI agents in a pipeline:

```
User Prompt → Orchestrator → Researcher → Narrative → Designer → PPTX
                    ↓            ↓            ↓          ↓
                  LLM         Web Search    LLM       Layout
```

### Agent Responsibilities

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Orchestrator** | Plans slide structure | User prompt | JSON deck structure with slide titles/types |
| **Researcher** | Gathers information | Prompt + slide topics | Research results + key insights |
| **Narrative** | Generates content | Research context | Slide body text, bullet points, callouts |
| **Designer** | Calculates layouts | Slide content | X, Y, width, height coordinates |
| **Visual QA** | Inspects quality | Rendered slides | Feedback on visual issues |

---

## Code Structure

```
ai-presentation-cli/
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── orchestrator.py       # Plans presentation structure
│   ├── researcher.py         # Web research + synthesis
│   ├── narrative.py          # Content generation
│   ├── designer.py           # Layout calculations
│   └── visual_qa.py          # Visual quality checks
│
├── compiler/                  # Output generators
│   ├── __init__.py
│   ├── pptx_builder.py       # PowerPoint file generation
│   └── playwright_renderer.py # Slide rendering for QA
│
├── core/                      # Core utilities
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── llm.py                # LLM proxy wrapper
│   └── state.py               # State definitions
│
├── tools/                     # External tool integrations
│   ├── __init__.py
│   └── search.py             # Tavily web search
│
├── graph.py                   # LangGraph pipeline definition
├── cli.py                     # Command-line interface
├── config.yaml                # Configuration file
└── requirements.txt           # Python dependencies
```

---

## How It Works

### 1. User Input
```bash
python cli.py generate "AI in Healthcare" --output presentation.pptx
```

### 2. Orchestrator Agent
The orchestrator uses an LLM to create a structured plan:
```python
# Input: "Create a presentation about AI in Healthcare"
# Output:
{
  "slides": [
    {"title": "AI in Healthcare", "type": "title"},
    {"title": "What is AI in Healthcare?", "type": "content"},
    {"title": "Applications", "type": "bullet_points"},
    {"title": "Benefits", "type": "comparison"},
    {"title": "Conclusion", "type": "closing"}
  ]
}
```

### 3. Researcher Agent
Uses Tavily API to search the web and gather insights:
```python
search_results = tavily.search("AI healthcare applications 2024")
# Returns: [{title, url, content}, ...]
```

### 4. Narrative Agent
Generates slide content using the LLM:
```python
# For each slide:
{
  "heading": "AI Diagnostics",
  "body_text": "AI algorithms can analyze medical images...",
  "bullet_points": ["95% accuracy in CT scans", "Faster diagnosis"],
  "callout": "AI could save $150B in healthcare costs"
}
```

### 5. Designer Agent
Assigns spatial coordinates to each element:
```python
{
  "layout": {
    "elements": [
      {"type": "heading", "x": 0.5, "y": 0.5, "width": 12, "height": 0.8},
      {"type": "body", "x": 0.5, "y": 1.8, "width": 12, "height": 3}
    ]
  }
}
```

### 6. PPTX Compiler
Uses python-pptx to create the final file:
```python
from pptx import Presentation
prs = Presentation()
slide = prs.slides.add_slide(layout)
slide.shapes.title.text = "Slide Title"
prs.save("output.pptx")
```

---

## Setting Up Development Environment

### Prerequisites
- Python 3.10+
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Kaizen3424/Ppt-maker.git
cd Ppt-maker
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Required API Keys

1. **LLM Proxy**: Configure in `config.yaml`
```yaml
llm_proxy:
  base_url: "https://your-proxy-url/v1"
  api_key: "your-api-key"
```

2. **Tavily Search** (optional, for research):
```yaml
tavily:
  api_key: "your-tavily-key"
```

---

## Configuration

### config.yaml Structure

```yaml
# LLM Proxy Settings
llm_proxy:
  base_url: "https://proxyapi-virid.vercel.app/v1"
  api_key: "sk-random"

# Tavily Search API Key
tavily:
  api_key: "tvly-xxx"

# Model routing per agent
llm_routing:
  orchestrator_agent:
    provider: "openai"
    model: "moonshotai/kimi-k2-instruct-0905"
  
  researcher_agent:
    provider: "openai"
    model: "moonshotai/kimi-k2-instruct-0905"
  
  # ... other agents

# Search configuration
search:
  tavily:
    max_results: 5

# Visual QA configuration
visual_qa:
  max_iterations: 3
  screenshot_width: 1280
  screenshot_height: 720
```

### Changing Models

To use a different model, update the `model` field in `llm_routing`:
```yaml
llm_routing:
  orchestrator_agent:
    model: "anthropic/claude-3-sonnet"
```

---

## Running the Project

### Basic Usage
```bash
python cli.py generate "Your presentation topic" --output presentation.pptx
```

### With Custom Config
```bash
python cli.py generate "Topic" --config path/to/config.yaml --output file.pptx
```

### Available CLI Commands
```bash
# Generate presentation
python cli.py generate "Topic" --output out.pptx

# Show help
python cli.py --help
```

---

## Testing

### Test Single Component

```bash
# Test LLM connection
python -c "
from core.llm import get_llm
from core.config import get_config
config = get_config()
llm = get_llm(config.get_llm_config('orchestrator'), config.get_proxy_config())
print(llm.invoke('Hello').content)
"

# Test search
python -c "
from tools.search import get_search_tool
search = get_search_tool(max_results=3, api_key='tvly-xxx')
print(search.search('AI trends'))
"

# Test PPTX generation
python -c "
from compiler.pptx_builder import generate_pptx
result = generate_pptx({'slides': [{'title': 'Test', 'type': 'title'}]}, 'test.pptx')
print(f'Created: {result}')
"
```

### Test Full Pipeline

```bash
python -c "
from graph import build_graph
graph = build_graph()
result = graph.invoke({
    'prompt': 'Your topic',
    'metadata': {},
    'json_deck': {'slides': []},
    'errors': [],
    'current_agent': 'Starting...'
})
print(f'Slides: {len(result[\"json_deck\"][\"slides\"])}')
"
```

---

## Extending the Project

### Adding a New Agent

1. Create `agents/new_agent.py`:
```python
def new_agent(state, config):
    # Process state
    state['current_agent'] = 'New Agent'
    # Add your logic
    return state
```

2. Register in `agents/__init__.py`:
```python
from .new_agent import new_agent
```

3. Add to `graph.py` pipeline:
```python
from agents import new_agent
# Add to graph workflow
```

### Adding New Output Formats

To add PDF or HTML output:

1. Create `compiler/pdf_builder.py` or `compiler/html_builder.py`
2. Implement `generate_pdf()` or `generate_html()` function
3. Add CLI command in `cli.py`

### Adding New Search Providers

To add Google, Bing, or DuckDuckGo:

1. Create `tools/new_search.py`
2. Implement `search()` and `research()` methods
3. Update `agents/researcher.py` to use the new tool

---

## Troubleshooting

### Common Issues

**1. "No module named 'pptx'"**
```bash
pip install python-pptx
```

**2. "Tavily API key not found"**
- Ensure `tavily.api_key` is set in `config.yaml`
- Or set environment variable: `export TAVILY_API_KEY=your-key`

**3. "LLM connection failed"**
- Check `llm_proxy.base_url` in config.yaml
- Verify your API key is valid
- Check network connectivity

**4. "Empty PPTX file"**
- Check python-pptx is installed correctly
- Run: `python -c "from pptx import Presentation; print('OK')"`

**5. "JSON parse error"**
- The LLM may have returned malformed JSON
- Check agent prompts in `agents/*.py`
- Review logs for specific errors

### Debug Mode

Add verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. Check the [GitHub Issues](https://github.com/Kaizen3424/Ppt-maker/issues)
2. Review the code comments
3. Check LangChain and python-pptx documentation

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test
4. Commit with descriptive messages
5. Push to your fork and create a PR

---

## License

MIT License - Feel free to use and modify!
