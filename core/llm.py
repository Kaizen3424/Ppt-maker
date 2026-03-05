"""LLM helper functions for the presentation agents."""
from typing import Dict, Any, Optional

import os


def get_llm(config: Dict[str, str], proxy_config: Optional[Dict[str, str]] = None):
    """Get LLM client based on configuration.
    
    Args:
        config: LLM configuration with provider and model
        proxy_config: Optional proxy configuration with base_url and api_key
        
    Returns:
        LLM client instance
    """
    provider = config.get("provider", "openai")
    model = config.get("model", "moonshotai/kimi-k2-instruct-0905")
    
    # Get proxy settings
    base_url = None
    api_key = None
    
    if proxy_config:
        base_url = proxy_config.get("base_url")
        api_key = proxy_config.get("api_key")
    
    # Also check environment variables
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "sk-random")
    
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key
        )
    else:
        from langchain_openai import ChatOpenAI
        
        # Build kwargs
        kwargs = {
            "model": model,
            "api_key": api_key,
        }
        
        # Add base_url if proxy is configured
        if base_url:
            kwargs["base_url"] = base_url
        
        return ChatOpenAI(**kwargs)
