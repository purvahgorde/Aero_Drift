"""Configuration loading for AeroDrift.

Provides a clean interface for loading and accessing project configuration
from a YAML file.  Other modules can use this to obtain configuration values
without hardcoding them.

Usage::

    from app.config import load_config, ConfigError

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}")

    print(config.app.name)        # "AeroDrift"
    print(config.aws.region)      # "us-east-1"
    print(config.get("missing"))  # None
"""

import os
import yaml


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ConfigError(Exception):
    """Raised when configuration cannot be loaded or is invalid."""
    pass


# ---------------------------------------------------------------------------
# Default values for optional configuration keys
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "app": {
        "name": "AeroDrift",
        "description": "Cloud Topology & Remediation Platform",
        "version": "0.0.0",
    },
    "aws": {
        "region": "us-east-1",
        "mock_data_path": "data/mock_aws_state.json",
    },
    "logging": {
        "level": "INFO",
        "verbose": False,
    },
}

# Keys that must be present in the configuration file
_REQUIRED_KEYS = ["app"]
_REQUIRED_APP_KEYS = ["name"]


# ---------------------------------------------------------------------------
# AeroConfig — nested attribute-access wrapper
# ---------------------------------------------------------------------------

class AeroConfig:
    """Lightweight wrapper that allows attribute access to configuration values.

    Nested dictionaries are automatically converted to ``AeroConfig``
    instances so that ``config.aws.region`` works as expected.

    Supports dict-style access (``config["aws"]``), ``.get()`` with a
    default, and iteration over top-level keys.
    """

    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, AeroConfig(value))
            else:
                setattr(self, key, value)
        # Keep the raw dict for serialisation / iteration
        self._data = data

    def get(self, key, default=None):
        """Return the value for *key*, or *default* if not present."""
        return getattr(self, key, default)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __contains__(self, key):
        return hasattr(self, key) and key != "_data"

    def keys(self):
        """Return top-level configuration keys."""
        return [k for k in self._data.keys()]

    def to_dict(self):
        """Return the configuration as a plain dictionary."""
        return dict(self._data)

    def __repr__(self):
        return f"AeroConfig({self._data!r})"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _resolve_default_path():
    """Resolve the default config.yaml path relative to the project root.

    Uses the same pattern as ``collector.py`` — walk up from app/ to find
    the project root.
    """
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    return os.path.join(project_root, "config.yaml")


def _merge_defaults(data: dict) -> dict:
    """Fill in missing optional keys with default values."""
    merged = dict(_DEFAULTS)
    for section, defaults in _DEFAULTS.items():
        if isinstance(defaults, dict):
            user_section = data.get(section, {})
            if isinstance(user_section, dict):
                merged_section = dict(defaults)
                merged_section.update(user_section)
                merged[section] = merged_section
            else:
                merged[section] = user_section
        else:
            merged[section] = data.get(section, defaults)

    # Preserve any extra top-level keys the user added
    for key in data:
        if key not in merged:
            merged[key] = data[key]

    return merged


def _validate(data: dict):
    """Validate that required configuration keys are present.

    Raises ``ConfigError`` with a human-readable message on failure.
    """
    for key in _REQUIRED_KEYS:
        if key not in data:
            raise ConfigError(
                f"Missing required configuration section: '{key}'"
            )

    app_section = data.get("app", {})
    if not isinstance(app_section, dict):
        raise ConfigError(
            "Configuration section 'app' must be a mapping (dictionary)"
        )

    for key in _REQUIRED_APP_KEYS:
        if key not in app_section:
            raise ConfigError(
                f"Missing required configuration key: 'app.{key}'"
            )


def load_config(path=None):
    """Load configuration from a YAML file and return an ``AeroConfig``.

    Parameters
    ----------
    path : str or None
        Path to the YAML configuration file.  When *None*, the default
        ``config.yaml`` at the project root is used.

    Returns
    -------
    AeroConfig
        A configuration object with attribute access to all values.

    Raises
    ------
    ConfigError
        If the file is missing, contains invalid YAML, or is missing
        required configuration keys.
    """
    if path is None:
        path = _resolve_default_path()

    # --- Check file exists ---
    if not os.path.isfile(path):
        raise ConfigError(f"Configuration file not found: {path}")

    # --- Read and parse YAML ---
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in configuration file: {exc}")

    # --- Handle empty file ---
    if data is None or not isinstance(data, dict):
        raise ConfigError(
            "Configuration file is empty or does not contain a valid mapping"
        )

    # --- Validate required keys ---
    _validate(data)

    # --- Merge with defaults ---
    merged = _merge_defaults(data)

    return AeroConfig(merged)
