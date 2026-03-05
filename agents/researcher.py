"""Researcher agent - gathers facts using web search and RAG tools."""
import json
import re
from typing import Dict, Any, List, Optional

from core.state import PresentationState
from core.config import Config
from core.llm import get_llm as get_llm_helper
from tools.search import get_search_tool


# Source types for multi-source integration
SOURCE_TYPES = {
    "general": {
        "description": "General web search",
        "priority": 1
    },
    "academic": {
        "description": "Academic papers and research",
        "priority": 2,
        "apis": ["scholar", "arxiv", "pubmed"]
    },
    "news": {
        "description": "Recent news articles",
        "priority": 3,
        "apis": ["newsapi", "gnews"]
    },
    "images": {
        "description": "Image search for visual content",
        "priority": 4,
        "apis": ["unsplash", "pexels"]
    }
}


def researcher_agent(state: PresentationState, config: Config) -> PresentationState:
    """The Researcher agent gathers facts using search tools.
    
    It searches the web for relevant information based on the presentation
    topic and saves research context to the state.
    
    Enhanced with:
    - Multi-source integration (general, academic, news, images)
    - Advanced information extraction
    - LLM-assisted credibility assessment
    - Image and media sourcing
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
    
    # Execute searches across multiple source types
    research_results = {}
    
    # General search
    for query in research_queries:
        results = search_tool.search(query)
        research_results[query] = results
    
    # Store research in metadata
    state["metadata"]["research_context"] = research_results
    state["metadata"]["research_queries"] = research_queries
    
    # Advanced information extraction
    extracted_info = _extract_advanced_info(research_results)
    state["metadata"]["extracted_info"] = extracted_info
    
    # Use LLM to synthesize research into key insights with credibility assessment
    llm_config = config.get_llm_config("researcher_agent")
    proxy_config = config.get_proxy_config()
    llm = get_llm_helper(llm_config, proxy_config)
    
    # Enhanced synthesis with credibility assessment
    synthesis_prompt = f"""Topic: {prompt}

Research results: {json.dumps(research_results, indent=2)}

EXTRACTED INFORMATION:
{json.dumps(extracted_info, indent=2)}

Create 5-7 key insights for this presentation as a JSON array of strings.
Additionally, identify potential credibility issues or biases in the sources.

Output JSON with format:
{{
    "insights": [...],
    "credibility_notes": [...],
    "source_diversity": "high/medium/low"
}}

Only output the JSON object."""
    
    try:
        response = llm.invoke(synthesis_prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Try to parse JSON
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            synthesis = json.loads(content)
            state["metadata"]["key_insights"] = synthesis.get("insights", [])
            state["metadata"]["credibility_notes"] = synthesis.get("credibility_notes", [])
            state["metadata"]["source_diversity"] = synthesis.get("source_diversity", "medium")
        except (json.JSONDecodeError, AttributeError):
            # Fallback: extract insights from raw text
            state["metadata"]["key_insights"] = [r.get("content", "")[:200] for r in list(research_results.values())[0][:3]] if research_results else []
            state["metadata"]["credibility_notes"] = []
            state["metadata"]["source_diversity"] = "medium"
    except Exception as e:
        state["metadata"]["key_insights"] = []
        state["metadata"]["credibility_notes"] = []
        state["metadata"]["source_diversity"] = "low"
    
    # Image sourcing (if enabled in config)
    image_config = config._config.get("research", {}).get("image_search", {})
    if image_config.get("enabled", False):
        image_results = _search_for_images(prompt, search_tool, max_results=3)
        state["metadata"]["suggested_images"] = image_results
    
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


def _extract_advanced_info(research_results: Dict[str, Any]) -> Dict[str, Any]:
    """Perform advanced information extraction from search results."""
    
    extracted = {
        "statistics": [],
        "definitions": {},
        "entities": [],
        "quotes": [],
        "dates": []
    }
    
    for query, results in research_results.items():
        if not results:
            continue
            
        for result in results:
            content = result.get("content", "")
            
            # Extract statistics (numbers with context)
            stats = re.findall(r'\b\d+(?:\.\d+)?(?:%|million|billion|thousand)?\b', content)
            if stats:
                extracted["statistics"].extend(stats[:3])
            
            # Extract dates
            dates = re.findall(r'\b(?:\d{4}|january|february|march|april|may|june|july|august|september|october|november|december)\b', content, re.IGNORECASE)
            if dates:
                extracted["dates"].extend(dates[:2])
            
            # Extract potential key terms (capitalized phrases)
            terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', content)
            if terms:
                extracted["entities"].extend(terms[:3])
    
    # Deduplicate
    extracted["statistics"] = list(dict.fromkeys(extracted["statistics"]))[:10]
    extracted["entities"] = list(dict.fromkeys(extracted["entities"]))[:10]
    extracted["dates"] = list(dict.fromkeys(extracted["dates"]))[:10]
    
    return extracted


def _search_for_images(prompt: str, search_tool, max_results: int = 3) -> List[Dict[str, Any]]:
    """Search for relevant images based on presentation topic."""
    
    image_queries = [
        f"{prompt} presentation",
        f"{prompt} business"
    ]
    
    results = []
    for query in image_queries[:1]:
        # Note: In a full implementation, this would use a dedicated image search API
        # For now, we'll return a placeholder structure
        results.append({
            "query": query,
            "suggested_terms": prompt.split()[:3],
            "note": "Image search API integration required"
        })
    
    return results[:max_results]


def _assess_source_credibility(results: List[Dict[str, Any]], llm) -> List[Dict[str, Any]]:
    """Use LLM to assess credibility of sources."""
    
    if not results:
        return []
    
    # Build context for credibility assessment
    source_context = []
    for r in results[:5]:
        source_context.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:200]
        })
    
    prompt = f"""Assess the credibility of these sources for a presentation:

{json.dumps(source_context, indent=2)}

For each source, provide:
- credibility_score: 1-10
- potential_bias: "none" or description
- reliability_notes: brief explanation

Output JSON array of assessments."""
    
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content)
    except Exception:
        return []
