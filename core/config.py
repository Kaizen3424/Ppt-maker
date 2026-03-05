"""Configuration management for the AI presentation CLI."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class Config:
    """Configuration manager that loads from config.yaml."""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to config.yaml in project root
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # Use default config if file doesn't exist
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "llm_proxy": {
                "base_url": "https://proxyapi-virid.vercel.app/v1",
                "api_key": "sk-random"
            },
            "llm_routing": {
                "orchestrator_agent": {
                    "provider": "openai",
                    "model": "moonshotai/kimi-k2-instruct-0905"
                },
                "researcher_agent": {
                    "provider": "openai",
                    "model": "moonshotai/kimi-k2-instruct-0905"
                },
                "narrative_agent": {
                    "provider": "openai",
                    "model": "moonshotai/kimi-k2-instruct-0905"
                },
                "design_agent": {
                    "provider": "openai",
                    "model": "moonshotai/kimi-k2-instruct-0905"
                },
                "vision_qa_agent": {
                    "provider": "openai",
                    "model": "moonshotai/kimi-k2-instruct-0905"
                }
            }
        }
    
    def get_llm_config(self, agent_name: str) -> Dict[str, str]:
        """Get LLM configuration for a specific agent."""
        return self._config.get("llm_routing", {}).get(agent_name, {})
    
    def get_provider(self, agent_name: str) -> str:
        """Get the provider for an agent."""
        return self.get_llm_config(agent_name).get("provider", "openai")
    
    def get_model(self, agent_name: str) -> str:
        """Get the model for an agent."""
        return self.get_llm_config(agent_name).get("model", "moonshotai/kimi-k2-instruct-0905")
    
    def get_proxy_config(self) -> Dict[str, str]:
        """Get proxy configuration for LLM calls."""
        return self._config.get("llm_proxy", {})
    
    def get_tavily_config(self) -> Dict[str, str]:
        """Get Tavily search configuration."""
        return self._config.get("tavily", {})


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reload_config(config_path: str) -> Config:
    """Force reload config from a specific path."""
    global _config
    _config = Config(config_path)
    return _config
