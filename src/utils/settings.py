from pathlib import Path
from typing import Any, cast

import yaml


def load_settings(config_path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    """
    Load project settings from YAML.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Settings config not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_settings: Any = yaml.safe_load(file)

    if raw_settings is None:
        return {}

    if not isinstance(raw_settings, dict):
        raise TypeError(f"Settings config must be a dictionary: {path}")

    return cast(dict[str, Any], raw_settings)


def get_required_categories(config_path: str | Path = "config/settings.yaml") -> list[str]:
    """
    Return required condition engine categories from project settings.
    """
    settings = load_settings(config_path)
    categories = settings["engine"]["required_categories"]

    if not isinstance(categories, list):
        raise TypeError("engine.required_categories must be a list")

    return [str(category) for category in categories]


def get_minimum_required_signals(config_path: str | Path = "config/settings.yaml") -> int:
    """
    Return the minimum number of usable signals required for classification.
    """
    settings = load_settings(config_path)
    minimum_required_signals = settings["engine"]["minimum_required_signals"]

    return int(minimum_required_signals)