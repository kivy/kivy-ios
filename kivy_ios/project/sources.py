"""Render the fixed source files and the per-project ``main_config.h`` (spec 06).

Generated source layout in <app>-ios/:
  main.m                  — trivial entry point; calls kivy_ios_main()
  kivy_ios_bootstrap.h    — bootstrap public header
  kivy_ios_bootstrap.m    — dual-mode bootstrap (SDL3 for Kivy, UIKit for pure-Python)
  main_config.h           — per-project defines (entry point, py version)
  platform/ios.py         — Kivy iOS platform shim (DPI, scale, safe area, keyboard)
  platform/mobile.py      — kivy.mobile API preview / cross-platform bridge
"""

from __future__ import annotations

from pathlib import Path

from ..config.model import Config

_TEMPLATES = Path(__file__).parent / "templates"

# Files that are copied verbatim from templates/ into the generated project.
_BOOTSTRAP_FILES = ("kivy_ios_bootstrap.h", "kivy_ios_bootstrap.m")


def main_m_source() -> str:
    return (_TEMPLATES / "main.m").read_text(encoding="utf-8")


def render_main_config_h(config: Config, *, python_version: str | None = None) -> str:
    """Fill the main_config.h template with APP_DIR / ENTRY_POINT / py version.

    ``app/`` is the symlink name inside ``<app>-ios/`` (always ``app``), so
    APP_DIR is the bundle-relative folder name, not the user's ``app_dir`` path.
    """
    version = (
        python_version
        or (config.ios.python_version if config.ios else None)
        or "3.15.0"
    )
    major_minor = ".".join(version.split(".")[:2])
    template = (_TEMPLATES / "main_config.h.in").read_text(encoding="utf-8")
    return (
        template.replace("@APP_DIR@", "app")
        .replace("@ENTRY_POINT@", config.kivy.entry_point)
        .replace("@PYTHON_MAJOR_MINOR@", major_minor)
    )


def ios_shim_source() -> str:
    return (_TEMPLATES / "ios.py").read_text(encoding="utf-8")


def mobile_shim_source() -> str:
    return (_TEMPLATES / "mobile.py").read_text(encoding="utf-8")


def write_platform_shim(project_dir: str | Path) -> Path:
    """Materialize ``platform/ios.py`` for Kivy metrics on iOS."""
    platform_dir = Path(project_dir) / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)
    shim = platform_dir / "ios.py"
    shim.write_text(ios_shim_source(), encoding="utf-8")
    return shim


def write_mobile_shim(project_dir: str | Path) -> Path:
    """Materialize ``platform/mobile.py`` — the kivy.mobile API preview."""
    platform_dir = Path(project_dir) / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)
    shim = platform_dir / "mobile.py"
    shim.write_text(mobile_shim_source(), encoding="utf-8")
    return shim


def write_sources(
    config: Config, project_dir: str | Path, *, python_version: str | None = None
) -> tuple[Path, Path]:
    project_dir = Path(project_dir)
    main_m = project_dir / "main.m"
    main_h = project_dir / "main_config.h"
    main_m.write_text(main_m_source(), encoding="utf-8")
    main_h.write_text(
        render_main_config_h(config, python_version=python_version), encoding="utf-8"
    )
    for fname in _BOOTSTRAP_FILES:
        (project_dir / fname).write_text(
            (_TEMPLATES / fname).read_text(encoding="utf-8"), encoding="utf-8"
        )
    write_platform_shim(project_dir)
    write_mobile_shim(project_dir)
    return main_m, main_h
