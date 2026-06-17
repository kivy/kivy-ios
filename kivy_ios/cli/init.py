"""``toolchain init`` — smart project initialization (spec 05).

One write path:

* **update** — a ``pyproject.toml`` exists. Only add/replace ``[tool.kivy*]``;
  ``[project]`` and every other namespace are left untouched. No venv required.

If ``requirements.txt`` is found but no ``pyproject.toml``, init exits non-zero
with a migration pointer rather than auto-migrating.
"""

from __future__ import annotations

import sys
import tomllib
from importlib import metadata
from pathlib import Path

import click

from ..config.model import SigningConfig
from ._common import PYPROJECT_NAME, ToolchainError
from .init_writer import (
    append_kivy_tables,
    has_kivy_dep,
    has_kivy_ios_table,
    normalize_package_name,
    strip_kivy_tables,
)

REQUIREMENTS_NAME = "requirements.txt"

_REQUIREMENTS_MSG = (
    "requirements.txt found but no pyproject.toml.\n"
    "  kivy-ios requires pyproject.toml — it will not migrate requirements.txt\n"
    "  automatically. Transfer your dependencies to a new pyproject.toml:\n\n"
    "    [project]\n"
    '    name = "myapp"  # your app name\n'
    '    version = "0.1.0"\n'
    "    dependencies = [\n"
    '        "kivy>=3.0",\n'
    "        # ... paste your other requirements here\n"
    "    ]\n\n"
    "  Then re-run toolchain init."
)


@click.command()
@click.option(
    "--force", is_flag=True, help="Regenerate [tool.kivy*] (preserves signing)."
)
def init(force: bool) -> None:
    """Seed [tool.kivy] / [tool.kivy.ios] into pyproject.toml."""
    cwd = Path.cwd()
    pyproject = cwd / PYPROJECT_NAME
    requirements = cwd / REQUIREMENTS_NAME

    if pyproject.is_file():
        _run_update_path(pyproject, force=force)
    elif requirements.is_file():
        raise ToolchainError(_REQUIREMENTS_MSG)
    else:
        raise ToolchainError(
            f"no {PYPROJECT_NAME} found in {cwd}.\n"
            f"  Create a minimal {PYPROJECT_NAME} with your app's metadata, then re-run:\n\n"
            f"    [project]\n"
            f'    name = "myapp"\n'
            f'    version = "0.1.0"\n'
            f"    dependencies = [\n"
            f'        "kivy>=3.0",\n'
            f"    ]\n\n"
            f"  See https://packaging.python.org/tutorials/packaging-projects/ for details."
        )


def _run_update_path(pyproject: Path, *, force: bool) -> None:
    text = pyproject.read_text(encoding="utf-8")
    raw = _safe_parse(text, pyproject)

    if "project" not in raw:
        raise ToolchainError(
            f"{PYPROJECT_NAME} has no [project] table.\n"
            "  init updates only [tool.kivy*]; it will not author [project] for "
            "an existing file. Add a minimal [project] (name + version) first."
        )

    existing_ios = has_kivy_ios_table(text)
    if existing_ios and not force:
        raise ToolchainError(
            "[tool.kivy.ios] already exists. Re-run with --force to regenerate "
            "it (your [tool.kivy.ios.signing] is preserved)."
        )

    app_slug = _project_slug(raw)
    deps = raw.get("project", {}).get("dependencies", [])
    kivy = has_kivy_dep(deps) if isinstance(deps, list) else False

    if existing_ios and force:
        signing = _read_signing(raw)
        python_version = _read_python_version(raw)
        stripped = strip_kivy_tables(text)
        new_text = append_kivy_tables(
            stripped,
            app_slug,
            signing=signing,
            python_version=python_version,
            has_kivy=kivy,
        )
        pyproject.write_text(new_text, encoding="utf-8")
        click.echo("Regenerated [tool.kivy*] (signing + python version preserved).")
    else:
        new_text = append_kivy_tables(text, app_slug, signing=None, has_kivy=kivy)
        pyproject.write_text(new_text, encoding="utf-8")
        click.echo("Added [tool.kivy] + [tool.kivy.ios] to pyproject.toml.")

    _maybe_warn_drift(raw)
    click.echo("Next: fill in bundle_id / signing.team_id, then `toolchain lock`.")


# --------------------------------------------------------------------------- #
# environment probing
# --------------------------------------------------------------------------- #
def _venv_active() -> bool:
    return sys.prefix != sys.base_prefix


def _installed_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for dist in metadata.distributions():
        name = dist.metadata["Name"]
        if name:
            out[_canon(name)] = dist.version
    return out


def _canon(name: str) -> str:
    import re

    return re.sub(r"[-_.]+", "-", name).lower()


def _safe_parse(text: str, path: Path) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ToolchainError(f"{path} is not valid TOML: {exc}") from exc


def _project_slug(raw: dict) -> str:
    name = raw.get("project", {}).get("name")
    if isinstance(name, str) and name:
        return normalize_package_name(name)
    return "app"


def _read_python_version(raw: dict) -> str | None:
    try:
        version = raw["tool"]["kivy"]["ios"]["python"]["version"]
    except (KeyError, TypeError):
        return None
    return version if isinstance(version, str) and version else None


def _read_signing(raw: dict) -> SigningConfig | None:
    try:
        signing = raw["tool"]["kivy"]["ios"]["signing"]
    except (KeyError, TypeError):
        return None
    if not isinstance(signing, dict):
        return None
    return SigningConfig(
        team_id=signing.get("team_id", ""),
        identity=signing.get("identity", "Apple Development"),
        provisioning_profile=signing.get("provisioning_profile", ""),
        auto_signing=bool(signing.get("auto_signing", True)),
        upload_symbols=bool(signing.get("upload_symbols", True)),
    )


def _maybe_warn_drift(raw: dict) -> None:
    """If a venv is active, warn when an installed dep drifts from its specifier."""
    if not _venv_active():
        return
    deps = raw.get("project", {}).get("dependencies", [])
    if not isinstance(deps, list):
        return
    installed = _installed_versions()
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.version import Version

    for raw_req in deps:
        try:
            req = Requirement(raw_req)
        except InvalidRequirement:
            continue
        version = installed.get(_canon(req.name))
        if (
            version
            and str(req.specifier)
            and not req.specifier.contains(Version(version), prereleases=True)
        ):
            click.echo(
                f"warning: installed {req.name} {version} is outside declared "
                f"'{req.specifier}'. (Not modified.)",
                err=True,
            )
