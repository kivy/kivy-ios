"""Validate [tool.kivy.ios].find_links before lock resolution."""

from __future__ import annotations

import os
from pathlib import Path


class FindLinksError(Exception):
    """A find_links directory is missing or has no usable wheels."""


def resolve_find_links(project_root: Path, entries: tuple[str, ...]) -> list[str]:
    """Resolve repo-relative ``find_links`` entries to absolute paths."""
    root = project_root.resolve()
    return [str((root / entry).resolve()) for entry in entries]


def validate_find_links(project_root: Path, entries: tuple[str, ...]) -> None:
    """Raise ``FindLinksError`` when a find_links directory is missing or unusable."""
    if not entries:
        return

    root = project_root.resolve()
    lines: list[str] = []
    for entry in entries:
        path = (root / entry).resolve()
        rel = _display_path(root, path, entry)
        if not path.exists():
            lines.append(
                f"[tool.kivy.ios].find_links entry {entry!r} does not exist ({rel})."
            )
            continue
        if not path.is_dir():
            lines.append(
                f"[tool.kivy.ios].find_links entry {entry!r} is not a directory ({rel})."
            )
            continue
        if not any(path.glob("*.whl")):
            lines.append(
                f"[tool.kivy.ios].find_links entry {entry!r} contains no .whl files ({rel})."
            )

    if not lines:
        return

    hint = _find_links_hint(root, entries)
    message = "\n".join(lines)
    if hint:
        message = f"{message}\n{hint}"
    raise FindLinksError(message)


def wheel_path_from_project_root(project_root: Path, resolved: Path) -> str:
    """Return a project-root-relative wheel path (may contain ``..``)."""
    root = project_root.resolve()
    resolved = resolved.resolve()
    _ensure_find_link_scope(root, resolved)
    return Path(os.path.relpath(resolved, root)).as_posix()


def find_links_resolution_hint(
    project_root: Path,
    entries: tuple[str, ...],
    *,
    pip_stderr: str = "",
) -> str | None:
    """Return extra guidance when pip resolution likely failed for find_links reasons."""
    if not entries:
        return None

    root = project_root.resolve()
    pip_text = pip_stderr.lower()
    if (
        "no matching distribution" not in pip_text
        and "could not find a version" not in pip_text
    ):
        return None

    lines: list[str] = []
    for entry in entries:
        path = (root / entry).resolve()
        rel = _display_path(root, path, entry)
        if not path.exists():
            lines.append(f"  • {entry!r} → missing ({rel})")
        elif not path.is_dir():
            lines.append(f"  • {entry!r} → not a directory ({rel})")
        elif not any(path.glob("*.whl")):
            lines.append(
                f"  • {entry!r} → directory exists but has no .whl files ({rel})"
            )
        else:
            count = len(list(path.glob("*.whl")))
            lines.append(
                f"  • {entry!r} → {count} wheel(s) present ({rel}); "
                "none matched this iOS slice or dependency."
            )

    if not lines:
        return None

    return (
        "find_links check:\n"
        + "\n".join(lines)
        + "\n"
        + _find_links_hint(root, entries)
    )


def find_links_doctor_detail(
    project_root: Path, entry: str, path: Path
) -> tuple[str, str | None]:
    """Return (detail, hint) for a single find_links entry."""
    rel = _display_path(project_root.resolve(), path, entry)
    if not path.exists():
        return f"{entry!r} missing ({rel})", _find_links_hint(project_root, (entry,))
    if not path.is_dir():
        return f"{entry!r} is not a directory ({rel})", None
    wheels = list(path.glob("*.whl"))
    if not wheels:
        return f"{entry!r} has no .whl files ({rel})", _find_links_hint(
            project_root, (entry,)
        )
    return f"{entry!r} ({len(wheels)} wheel(s) in {rel})", None


def _find_links_hint(project_root: Path, entries: tuple[str, ...]) -> str:
    del entries  # reserved for future per-entry hints
    shared_note = ""
    if project_root.parent.name == "examples" and project_root.name != "wheels":
        shared_note = (
            "  Shared example wheels live under examples/wheels/ — run "
            "`scripts/build_ios_wheels.sh` from the repo root.\n"
        )
    return (
        f"{shared_note}"
        "  Add locally built iOS wheels to the directory, then re-run `toolchain lock`."
    )


def _display_path(project_root: Path, path: Path, entry: str) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return entry


def _ensure_find_link_scope(project_root: Path, resolved: Path) -> None:
    try:
        resolved.relative_to(project_root)
        return
    except ValueError:
        pass
    try:
        resolved.relative_to(project_root.parent)
    except ValueError as exc:
        raise FindLinksError(
            f"find_links path {resolved} is outside the project directory and "
            "its parent"
        ) from exc
