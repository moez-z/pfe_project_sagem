"""
core/app_config.py
------------------
Stores local machine configuration in a JSON file next to main.py.
This is per-machine config (post number, etc.) — not shared via DB.

Config file: <project_root>/app_config.json
"""

import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "app_config.json"

_DEFAULTS = {
    "post_number":   None,   # int 1-10, set on first launch
    "post_id":       None,   # DB id of the post
    "post_name":     None,   # e.g. "Caisson 3"
    "configured":    False,  # True after first setup is done
}


def load() -> dict:
    """Load config from disk. Returns defaults if file doesn't exist."""
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # merge with defaults in case new keys were added
            return {**_DEFAULTS, **data}
        except Exception as e:
            print(f"[config] Failed to read config: {e}")
    return dict(_DEFAULTS)


def save(cfg: dict):
    """Persist config to disk."""
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[config] Failed to save config: {e}")


def is_configured() -> bool:
    return load().get("configured", False)


def get_post_id() -> int | None:
    return load().get("post_id")


def get_post_name() -> str | None:
    return load().get("post_name")


def set_post(post_id: int, post_number: int, post_name: str):
    """Save the selected post to local config."""
    cfg = load()
    cfg["post_id"]     = post_id
    cfg["post_number"] = post_number
    cfg["post_name"]   = post_name
    cfg["configured"]  = True
    save(cfg)
    print(f"[config] Post configured: {post_name} (id={post_id})")