"""Create and maintain the ``<app>-ios/`` staging tree (spec 06)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..config.model import Config


class StagingError(Exception):
    """Staging tree cannot be created (e.g. ``app_dir`` does not exist)."""


@dataclass(frozen=True)
class StagingLayout:
    root: Path  # <app>-ios/

    @property
    def xcodeproj(self) -> Path:
        return self.root / f"{self.root.name[:-4]}.xcodeproj"

    @property
    def python_xcframework(self) -> Path:
        return self.root / "Python.xcframework"

    @property
    def frameworks(self) -> Path:
        return self.root / "Frameworks"

    @property
    def app(self) -> Path:
        return self.root / "app"

    @property
    def pip_deps_simulator(self) -> Path:
        return self.root / "pip-deps-simulator"

    @property
    def pip_deps_device(self) -> Path:
        return self.root / "pip-deps-device"

    def pip_deps_for_slice(self, target: str) -> Path:
        """Return the slice-specific pip-deps directory for *target*."""
        return (
            self.pip_deps_simulator if target == "simulator" else self.pip_deps_device
        )

    @property
    def resources(self) -> Path:
        return self.root / "Resources"


def staging_dir_name(config: Config) -> str:
    return f"{config.app_slug}-ios"


def create_staging(config: Config, project_root: str | Path) -> StagingLayout:
    """Create the ``<app>-ios/`` tree and the ``app/`` symlink to ``app_dir``.

    The symlink is created once and refreshed only if it points somewhere
    other than the current ``app_dir`` (spec 06 "symlink, not copy").
    """
    project_root = Path(project_root)
    root = project_root / staging_dir_name(config)
    layout = StagingLayout(root=root)

    for d in (
        root,
        layout.frameworks,
        layout.pip_deps_device,
        layout.pip_deps_simulator,
        layout.resources,
    ):
        d.mkdir(parents=True, exist_ok=True)

    _refresh_app_symlink(layout, project_root, config.kivy.app_dir)
    return layout


def _refresh_app_symlink(
    layout: StagingLayout, project_root: Path, app_dir: str
) -> None:
    source = project_root / app_dir
    if not source.is_dir():
        raise StagingError(
            f"app_dir '{app_dir}' is not an existing directory "
            f"(looked for {source}). Create it or fix [tool.kivy].app_dir in "
            f"pyproject.toml — it must point at your app's Python source."
        )
    # The symlink target is relative to <app>-ios/ (e.g. ../src).
    target = os.path.relpath(source.resolve(), layout.root)
    link = layout.app
    if link.is_symlink():
        if os.readlink(link) == target:
            return
        link.unlink()
    elif link.exists():
        raise FileExistsError(
            f"{link} exists and is not a symlink; remove it and re-run build."
        )
    link.symlink_to(target)
