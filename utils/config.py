import yaml
import os
from typing import Any, Dict

DEFAULT_CONFIG = {
    "concurrency": 5,
    "timeout": 30000,
    "ports": "80,443",
    "insecure": True,
    "tech": True,
    "extract_links": False,
    "proxy": None,
    "proxychains": False,
    "output_dir": "projects"
}

CONFIG_PATH = ".glint_config.yaml"

class GlintConfig:
    @staticmethod
    def load() -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if not os.path.exists(CONFIG_PATH):
            return DEFAULT_CONFIG
        
        try:
            with open(CONFIG_PATH, "r") as f:
                user_config = yaml.safe_load(f) or {}
                # Merge user config with defaults
                config = DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
        except Exception:
            return DEFAULT_CONFIG

    @staticmethod
    def save(config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except Exception:
            return False

    @staticmethod
    def set(key: str, value: Any):
        """Update a single configuration key."""
        config = GlintConfig.load()
        config[key] = value
        return GlintConfig.save(config)
