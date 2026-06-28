"""kivy-ios project configuration (pyproject.toml) model and loader (spec 01)."""

from __future__ import annotations

from .errors import ConfigError
from .loader import load_config, load_config_from_text
from .model import (
    Author,
    Config,
    IconConfig,
    IosConfig,
    KivyMeta,
    ProjectMeta,
    SigningConfig,
    SplashConfig,
    SwiftPackageDep,
    XcframeworkDep,
)

__all__ = [
    "ConfigError",
    "load_config",
    "load_config_from_text",
    "Author",
    "Config",
    "IconConfig",
    "IosConfig",
    "KivyMeta",
    "ProjectMeta",
    "SigningConfig",
    "SplashConfig",
    "SwiftPackageDep",
    "XcframeworkDep",
]
