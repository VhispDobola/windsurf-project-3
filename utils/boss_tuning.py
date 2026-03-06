"""
Boss difficulty profile loading helpers.
"""

import copy
import json
import os
from functools import lru_cache
from typing import Any, Dict


def _normalize_keys(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            normalized_key = int(key) if isinstance(key, str) and key.isdigit() else key
            out[normalized_key] = _normalize_keys(item)
        return out
    if isinstance(value, list):
        return [_normalize_keys(item) for item in value]
    return value


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


@lru_cache(maxsize=1)
def _load_profiles_file() -> Dict[str, Any]:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(root, "config", "boss_difficulty_profiles.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
            if isinstance(payload, dict):
                return _normalize_keys(payload)
    except Exception:
        return {}
    return {}


def load_boss_profile(boss_name: str, section: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load a boss profile section from config JSON and merge with fallback defaults.
    """
    profiles = _load_profiles_file()
    boss_data = profiles.get(boss_name, {})
    external = boss_data.get(section, {})
    if not isinstance(external, dict):
        return copy.deepcopy(fallback)
    return _deep_merge(fallback, external)
