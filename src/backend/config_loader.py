import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigLoader:
    """Loads and manages application configuration from YAML file"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            # Look for config file in multiple locations
            config_paths = [
                Path(__file__).parent.parent.parent / "config" / "app_settings.yaml",
                Path("config/app_settings.yaml"),
                Path("../../config/app_settings.yaml")
            ]
            
            config_file = None
            for path in config_paths:
                if path.exists():
                    config_file = path
                    break
            
            if config_file is None:
                raise FileNotFoundError("app_settings.yaml not found in any expected location")
            
            with open(config_file, 'r') as f:
                self._config = yaml.safe_load(f)
                print(f"Configuration loaded from: {config_file}")
                
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            # Fallback to default configuration
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback default configuration"""
        return {
            'application': {
                'name': 'SQL Cleanser',
                'version': '2.0.0'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'cors_enabled': True
            },
            'processing': {
                'max_batch_files': 50,
                'ai_timeout_seconds': 600,
                'max_sample_rows_for_analysis': 20
            },
            'ollama': {
                'host': 'http://localhost:11434',
                'model': 'llama3:8b',
                'max_tokens': 16384,
                'timeout_seconds': 600,
                'retry_attempts': 3
            },
            'data_quality': {
                'enable_fuzzy_matching': True,
                'similarity_threshold': 0.8,
                'enable_semantic_analysis': True,
                'primary_key_inference': 'ai_enhanced'
            },
            'output': {
                'results_directory': 'results',
                'include_ai_analysis': True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'ollama.model')"""
        try:
            keys = key_path.split('.')
            value = self._config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary"""
        return self._config

# Global configuration instance
config = ConfigLoader() 