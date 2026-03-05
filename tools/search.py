"""Web search tools for the presentation agent."""
import os
from typing import List, Dict, Any, Optional
from langchain_community.tools.tavily_search import TavilySearchResults


class SearchTool:
    """Wrapper for web search functionality."""
    
    def __init__(self, max_results: int = 5, api_key: Optional[str] = None):
        self.max_results = max_results
        self._tool = None
        self._api_key = api_key
        self._api_key_missing = False
    
    def _get_tool(self) -> Optional[TavilySearchResults]:
        """Lazy initialization of the search tool."""
        if self._api_key_missing:
            return None
        
        if self._tool is None:
            # Try to get API key from parameter, environment, or config
            api_key = self._api_key or os.environ.get("TAVILY_API_KEY")
            if not api_key:
                self._api_key_missing = True
                return None
            self._tool = TavilySearchResults(max_results=self.max_results, tavily_api_key=api_key)
        return self._tool
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Execute a web search and return results.
        
        Args:
            query: The search query string
            
        Returns:
            List of search results with title, url, and content
        """
        tool = self._get_tool()
        if tool is None:
            # Return empty results if no API key
            return [{"query": query, "content": "Search unavailable - no API key"}]
        
        try:
            results = tool.invoke(query)
            return results
        except Exception as e:
            return [{"error": str(e), "query": query}]
    
    def research(self, *queries: str) -> Dict[str, List[Dict[str, Any]]]:
        """Run multiple research queries.
        
        Args:
            *queries: Multiple search query strings
            
        Returns:
            Dictionary mapping queries to their results
        """
        research_results = {}
        for query in queries:
            research_results[query] = self.search(query)
        return research_results


def get_search_tool(max_results: int = 5, api_key: Optional[str] = None) -> SearchTool:
    """Factory function to create a search tool instance."""
    return SearchTool(max_results=max_results, api_key=api_key)
