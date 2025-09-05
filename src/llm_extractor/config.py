"""
Gets configurations from config.yaml/.yml file in root directory and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

# Determine config path at runtime: prefer config.yaml then config.yml in project root
ROOT = Path(__file__).resolve().parents[2]
p1 = ROOT / "config.yaml"
p2 = ROOT / "config.yml"

if p1.exists():
    YAML_CONFIG_PATH = p1
elif p2.exists():
    YAML_CONFIG_PATH = p2
else:
    YAML_CONFIG_PATH = None  # Will trigger a clear error when loading


def _load_yaml_config() -> dict:
    if YAML_CONFIG_PATH is None or not YAML_CONFIG_PATH.exists():
        raise FileNotFoundError("No config.yaml or config.yml found in project root.")

    with open(YAML_CONFIG_PATH, "r") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML config: {YAML_CONFIG_PATH}") from e


def _get_by_path(data: Any, dotted_key: str) -> Any:
    """Get nested value using dot notation, e.g., 'OPENROUTER.DEFAULT_MODEL'."""
    cur = data
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _deep_find_key(data: Any, target: str) -> Any:
    """Recursively search dict/list structure for the first occurrence of key 'target'."""
    if isinstance(data, dict):
        if target in data:
            return data[target]
        for v in data.values():
            found = _deep_find_key(v, target)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _deep_find_key(item, target)
            if found is not None:
                return found
    return None


def get_config(key: str) -> Optional[str]:
    """
    Get configuration value by key.

    Priority: Environment Variable > YAML Config (top-level, dot-path, then deep) > None

    Args:
        key: Configuration key (supports dot notation for nested config, e.g. 'OPENROUTER.DEFAULT_MODEL')

    Returns:
        Configuration value or None if not found
    """
    # Environment variable takes precedence
    env_value = os.environ.get(key)
    if env_value is not None:
        return env_value

    config = _load_yaml_config()

    # 1) Direct top-level lookup
    if isinstance(config, dict) and key in config:
        return config[key]

    # 2) Dot-path lookup (e.g., 'OPENROUTER.DEFAULT_MODEL')
    dot_val = _get_by_path(config, key)
    if dot_val is not None:
        return dot_val

    # 3) Deep search for key anywhere in nested structure (e.g., find 'DEFAULT_MODEL')
    deep_val = _deep_find_key(config, key)
    if deep_val is not None:
        return deep_val

    return None


if __name__ == "__main__":
    print("DEFAULT_MODEL =", get_config("DEFAULT_MODEL"))
