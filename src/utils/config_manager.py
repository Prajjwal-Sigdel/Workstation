"""
Configuration Manager
Loads default config and merges with user overrides
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    """Manages application configuration with defaults and user overrides"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.default_config_path = self.config_dir / "default_config.json"
        self.user_config_path = self.config_dir / "user_config.json"
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from default and user config files"""
        # Load defualt config (required)
        if not self.default_config_path.exists():
            raise FileNotFoundError(f"Default config not found: {self.default_config_path}")
        
        with open(self.default_config_path, 'r') as f:
            self._config = json.load(f)

        # Merget user config if exists (Optional)
        if self.user_config_path.exists():
            with open(self.user_config_path, 'r') as f:
                user_config = json.load(f)
                self._merge_config(self._config, user_config)

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Recursively merge override config into base config"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value using dot notation
        Example: config.get('camera.device_index')
        """

        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
            
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self._config.copy()
    
    def reload(self) -> None:
        """Reload configuration from disk"""
        self.load()

# Singleton instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get gloabal configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance