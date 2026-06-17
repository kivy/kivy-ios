"""Pluggable Python-runtime adapters (plan cross-cutting decision).

A ``PythonRuntime`` hides *where* the iOS Python comes from and *how* the
``.so`` -> ``.framework`` conversion is wired into the Xcode project:

* ``PythonOrgRuntime`` — python.org's ``Python.xcframework`` + ``install_python``
  helper (the spec's canonical target, Python 3.15). Specs 02/03/06 are the
  source of truth for this adapter.
* ``BeewareRuntime`` — BeeWare ``Python-Apple-support`` (3.13-era), an interim
  dev aid for early real simulator/device smoke tests while 3.15 iOS wheels
  mature. Behind the same interface, isolated so divergences don't leak.

See ``docs/dev/beeware-layout.md`` for the layout-divergence spike.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RuntimeArtifact:
    version: str
    url: str
    # Archive container; both runtimes ship a gzipped tarball today.
    archive_format: str = "tar.gz"


class PythonRuntime(Protocol):
    name: str

    def xcframework_artifact(self, version: str) -> RuntimeArtifact:
        """The downloadable Python.xcframework archive for ``version``."""
        ...

    def build_python_invocation(
        self, *, xcframework: str, app: str, pip_deps: str
    ) -> str:
        """The 'Build Python' Run Script body that wires .so -> .framework."""
        ...

    def ios_floor(self, version: str) -> str:
        """Minimum iOS deployment target supported by this runtime/version."""
        ...


class PythonOrgRuntime:
    """Canonical target: python.org Python.xcframework + ``install_python``."""

    name = "python.org"

    URL_TEMPLATE = (
        "https://www.python.org/ftp/python/{version}/"
        "python-{version}-iOS-XCframework.tar.gz"
    )
    _FLOORS = {"3.15": "13.0", "3.14": "13.0", "3.13": "12.0"}

    def xcframework_artifact(self, version: str) -> RuntimeArtifact:
        return RuntimeArtifact(
            version=version, url=self.URL_TEMPLATE.format(version=version)
        )

    def build_python_invocation(
        self, *, xcframework: str, app: str, pip_deps: str
    ) -> str:
        # python.org ships `install_python` inside the xcframework; it walks
        # `app/` + `pip-deps/`, converts each `.so` to a per-module framework,
        # and leaves a `.fwork` marker (Python 3.15 iOS docs §7.2.2 step 7).
        return f"install_python {xcframework} {app} {pip_deps}"

    def ios_floor(self, version: str) -> str:
        return self._FLOORS.get(_minor(version), "13.0")


class BeewareRuntime:
    """Interim dev runtime: BeeWare ``Python-Apple-support`` release assets.

    BeeWare ships per-minor support packages (e.g. ``Python-3.13-iOS-support.bN``)
    rather than per-patch python.org artifacts, and its framework-conversion
    flow differs from ``install_python`` (it relies on a stub binary +
    ``Resources/`` layout). This adapter exists so we can smoke-test the
    pbxproj/runtime path before the python.org 3.15 artifact + iOS wheels are
    fully usable; it is NOT the shipping default.
    """

    name = "beeware"

    URL_TEMPLATE = (
        "https://github.com/beeware/Python-Apple-support/releases/download/"
        "{minor}-{build}/Python-{minor}-iOS-support.{build}.tar.gz"
    )

    def __init__(self, *, build: str = "b1") -> None:
        self._build = build

    def xcframework_artifact(self, version: str) -> RuntimeArtifact:
        minor = _minor(version)
        return RuntimeArtifact(
            version=version,
            url=self.URL_TEMPLATE.format(minor=minor, build=self._build),
        )

    def build_python_invocation(
        self, *, xcframework: str, app: str, pip_deps: str
    ) -> str:
        # Documented divergence: BeeWare has no `install_python`. The adapter
        # would shim an equivalent conversion step; tracked in the spike doc.
        return f"# beeware-runtime: convert .so under {app} {pip_deps} (see beeware-layout.md)"

    def ios_floor(self, version: str) -> str:
        return "13.0"


def get_runtime(name: str = "python.org", **kwargs) -> PythonRuntime:
    if name in ("python.org", "pythonorg", "python_org"):
        return PythonOrgRuntime()
    if name == "beeware":
        return BeewareRuntime(**kwargs)
    raise ValueError(f"unknown python runtime {name!r} (expected python.org|beeware)")


def _minor(version: str) -> str:
    return ".".join(version.split(".")[:2])
