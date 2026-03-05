# AI Presentation CLI

A multi-agent AI system for automatically generating PowerPoint presentations using LangGraph agents and LLM-powered content generation.

## Features

- **5 LangGraph Agents**: Orchestrator, Researcher, Narrative, Designer, Visual QA
- **LLM Proxy Support**: Works with OpenAI-compatible APIs
- **Web Research**: Uses Tavily for gathering content
- **PPTX Generation**: Creates professional PowerPoint files
- **Rich CLI**: Beautiful terminal interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `config.yaml`:
   - Set your LLM proxy URL and API key
   - Add your Tavily search API key
   - Configure models per agent

## Usage

```bash
python cli.py generate "Your presentation topic" --output presentation.pptx
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# LLM Proxy Settings
llm_proxy:
  base_url: "https://your-proxy-url/v1"
  api_key: "your-api-key"

# Tavily Search API Key
tavily:
  api_key: "your-tavily-key"

# Model routing per agent
llm_routing:
  orchestrator_agent:
    provider: "openai"
    model: "moonshotai/kimi-k2-instruct-0905"
```

## Architecture

- **Orchestrator**: Plans slide structure
- **Researcher**: Gathers web research
- **Narrative**: Generates slide content
- **Designer**: Calculates layouts
- **Visual QA**: Inspects rendered slides
