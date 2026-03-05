"""Researcher agent - gathers facts using web search and RAG tools."""
import json
from typing import Dict, Any, List

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper
from tools.search import get_search_tool


def researcher_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Researcher agent gathers facts using search tools.
    
    It searches the web for relevant information based on the presentation
    topic and saves research context to the state.
    """
    state["current_agent"] = "Researcher: Gathering web and document data..."
    
    # Get search tool with API key from config
    search_config = config.get_tavily_config()
    max_results = config._config.get("search", {}).get("tavily", {}).get("max_results", 5)
    api_key = search_config.get("api_key")
    search_tool = get_search_tool(max_results=max_results, api_key=api_key)
    
    prompt = state["prompt"]
    slides = state["json_deck"].get("slides", [])
    
    # Generate research queries based on the prompt and slide topics
    research_queries = _generate_research_queries(prompt, slides)
    
    # Execute searches
    research_results = {}
    for query in research_queries:
        results = search_tool.search(query)
        research_results[query] = results
    
    # Store research in metadata
    state["metadata"]["research_context"] = research_results
    state["metadata"]["research_queries"] = research_queries
    
    # Use LLM to synthesize research into key insights
    llm_config = config.get_llm_config("researcher_agent")
    proxy_config = config.get_proxy_config()
    llm = get_llm_helper(llm_config, proxy_config)
    
    synthesis_prompt = f"""Topic: {prompt}

Research results: {json.dumps(research_results, indent=2)}

Create 5-7 key insights for this presentation as a JSON array of strings.
Only output the JSON array."""
    
    try:
        response = llm.invoke(synthesis_prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Try to parse JSON
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            insights = json.loads(content)
            state["metadata"]["key_insights"] = insights
        except (json.JSONDecodeError, AttributeError):
            # Fallback: extract from raw text
            state["metadata"]["key_insights"] = [r.get("content", "")[:200] for r in list(research_results.values())[0][:3]] if research_results else []
    except Exception as e:
        state["metadata"]["key_insights"] = []
    
    return state


def _generate_research_queries(prompt: str, slides: List[Dict[str, Any]]) -> List[str]:
    """Generate research queries based on the prompt and slide structure."""
    queries = [prompt]
    
    # Add specific queries based on slide topics
    for slide in slides:
        title = slide.get("title", "")
        if title and len(title) > 3:
            queries.append(f"{title} key information")
    
    # Keep queries unique and limit to 5
    unique_queries = list(dict.fromkeys(queries))[:5]
    return unique_queries
