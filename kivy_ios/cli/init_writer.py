"""Pure helpers for ``toolchain init`` (spec 05).

Kept side-effect-free (no filesystem, no venv probing) so they can be unit
tested directly. ``init.py`` orchestrates these with the real environment.

Init uses *text surgery* — it only ever adds/replaces
``[tool.kivy*]`` sections and leaves ``[project]`` and every other namespace
byte-for-byte intact. We deliberately do not round-trip the whole file through
a TOML writer (which would drop comments and reorder keys).
"""

from __future__ import annotations

import re

from packaging.requirements import InvalidRequirement, Requirement

from ..config.model import SigningConfig

# Default Python.xcframework version init seeds (spec 01).
DEFAULT_PYTHON_VERSION = "3.15.0b2"
DEFAULT_DEPLOYMENT_TARGET = "13.0"

# Exclude block emitted when kivy is a direct dependency.  Each entry is
# documented with the Kivy feature that requires it so users know which lines
# are safe to remove for their specific app.
_KIVY_EXCLUDE_LINES = [
    "# Kivy's wheel declares deps that are not needed at runtime on iOS.",
    "# Remove an entry only if your app actually uses that feature.",
    "exclude = [",
    "    # kivy-garden: the extension registry / download CLI.  Never needed at",
    "    # runtime on iOS (the App Store prohibits dynamic package installation).",
    "    # Individual garden widgets (e.g. kivy-garden.mapview) are separate",
    "    # packages — add them to [project].dependencies instead.",
    '    "kivy-garden",',
    "    # requests and its transitive deps (below) are used by",
    "    # kivy.network.urlrequest.UrlRequest *and* by kivy-garden.",
    "    # Remove these lines only if your app uses UrlRequest for HTTP calls.",
    '    "requests",',
    '    "certifi",',
    '    "charset-normalizer",',
    '    "idna",',
    '    "urllib3",',
    "    # docutils: required by the RSTDocument widget (kivy.uix.rst).",
    "    # Remove this line if your app uses RSTDocument.",
    '    "docutils",',
    "    # pygments: required by the CodeInput widget (kivy.uix.codeinput).",
    "    # Remove this line if your app uses CodeInput.",
    '    "pygments",',
    "    # NOTE: filetype is imported unconditionally by kivy/core/image/__init__.py",
    "    # and cannot be excluded regardless of which widgets you use.",
    "]",
]

_TABLE_HEADER = re.compile(r"^\s*\[\[?\s*(?P<key>[^\]]+?)\s*\]\]?\s*(#.*)?$")


def normalize_package_name(raw: str) -> str:
    """Normalize a directory name into a valid Python package name.

    Lowercase; hyphens/spaces/dots → underscores; drop other invalid chars;
    ensure it does not start with a digit.
    """
    name = raw.strip().lower()
    name = re.sub(r"[-\s.]+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "app"
    if name[0].isdigit():
        name = f"app_{name}"
    return name


def _canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def bundle_id_segment(app_slug: str) -> str:
    """Convert a Python ``app_slug`` into a valid bundle-identifier segment.

    Bundle identifiers are UTIs: only alphanumeric, hyphen, and period are
    allowed.  ``app_slug`` is a Python package name (underscores are valid
    there) so underscores are mapped to hyphens here.
    """
    seg = app_slug.replace("_", "-")
    seg = re.sub(r"[^A-Za-z0-9-]", "", seg)
    return seg.strip("-") or "app"


def has_kivy_dep(dependencies: list[str]) -> bool:
    """Return True if any entry in *dependencies* is the ``kivy`` package."""
    for dep in dependencies:
        try:
            name = Requirement(dep).name
        except InvalidRequirement:
            name = dep.split(";", 1)[0].split("[", 1)[0].strip()
        if _canon(name) == "kivy":
            return True
    return False


def render_kivy_tables(
    app_slug: str,
    signing: SigningConfig | None = None,
    *,
    python_version: str | None = None,
    has_kivy: bool = False,
) -> str:
    """Render the ``[tool.kivy]`` + ``[tool.kivy.ios]`` block.

    When ``signing`` is provided (the ``--force`` preserve path) its concrete
    values are emitted; otherwise a commented template invites the user to fill
    in ``team_id``. ``python_version`` overrides the default xcframework pin.
    When ``has_kivy`` is True a documented ``exclude`` block is included so
    users know which transitive Kivy deps are safe to drop for their app.
    """
    display = app_slug.replace("_", " ").title()
    lines = [
        "[tool.kivy]",
        f'display_name = "{display}"',
        'app_dir = "src"',
        'entry_point = "main"',
        'orientation = ["portrait"]',
        "",
        "[tool.kivy.ios]",
        "schema_version = 1",
        f'bundle_id = "org.example.{bundle_id_segment(app_slug)}"  '
        "# TODO: change to your reverse-DNS bundle identifier",
        "build = 1",
        f'deployment_target = "{DEFAULT_DEPLOYMENT_TARGET}"',
    ]
    if has_kivy:
        lines += [""] + _KIVY_EXCLUDE_LINES
    lines += [
        "",
        "[tool.kivy.ios.python]",
        f'version = "{python_version or DEFAULT_PYTHON_VERSION}"',
        "",
        "[tool.kivy.ios.signing]",
    ]
    if signing is not None:
        lines += [
            f'team_id = "{signing.team_id}"',
            f'identity = "{signing.identity}"',
            f'provisioning_profile = "{signing.provisioning_profile}"',
            f"auto_signing = {str(signing.auto_signing).lower()}",
            f"upload_symbols = {str(signing.upload_symbols).lower()}",
        ]
    else:
        lines += [
            '# team_id = "ABCDE12345"  '
            "# TODO: set your Apple Developer Team ID for device/release builds",
            "auto_signing = true",
        ]
    return "\n".join(lines) + "\n"


def has_kivy_ios_table(text: str) -> bool:
    """True if the text already declares a [tool.kivy.ios] table."""
    return _section_keys(text).intersection({"tool.kivy.ios"}) != set() or any(
        k.startswith("tool.kivy.ios.") for k in _section_keys(text)
    )


def _section_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        m = _TABLE_HEADER.match(line)
        if m:
            keys.add(m.group("key").strip())
    return keys


def strip_kivy_tables(text: str) -> str:
    """Remove every ``[tool.kivy]`` / ``[tool.kivy.*]`` section from the text.

    Used by ``--force`` before re-appending freshly rendered tables. Non-kivy
    sections (including ``[project]`` and other tool namespaces) are preserved
    verbatim.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    dropping = False
    for line in lines:
        m = _TABLE_HEADER.match(line.rstrip("\n"))
        if m:
            key = m.group("key").strip()
            dropping = key == "tool.kivy" or key.startswith("tool.kivy.")
            if dropping:
                continue
        if dropping:
            continue
        out.append(line)
    result = "".join(out).rstrip("\n")
    return result + "\n" if result else ""


def append_kivy_tables(
    text: str,
    app_slug: str,
    signing: SigningConfig | None = None,
    *,
    python_version: str | None = None,
    has_kivy: bool = False,
) -> str:
    """Append freshly rendered kivy tables to existing pyproject text."""
    base = text.rstrip("\n")
    block = render_kivy_tables(
        app_slug, signing, python_version=python_version, has_kivy=has_kivy
    )
    return f"{base}\n\n{block}"
