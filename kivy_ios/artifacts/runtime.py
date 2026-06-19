"""Pluggable Python-runtime adapter (plan cross-cutting decision).

``PythonOrgRuntime`` provides the canonical iOS Python xcframework from
python.org (3.15+). The ``PythonRuntime`` Protocol keeps the interface
stable if a second runtime is ever needed.

See specs 02/03/06 for the canonical target details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RuntimeArtifact:
    version: str
    url: str
    # Archive container; python.org ships a gzipped tarball.
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


class PythonOrgRuntime:
    """Canonical runtime: python.org Python.xcframework + ``install_python``."""

    name = "python.org"

    URL_TEMPLATE = (
        "https://www.python.org/ftp/python/{version}/"
        "python-{version}-iOS-XCframework.tar.gz"
    )

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


def get_runtime(name: str = "python.org", **kwargs) -> PythonRuntime:
    if name in ("python.org", "pythonorg", "python_org"):
        return PythonOrgRuntime()
    raise ValueError(f"unknown python runtime {name!r} (expected python.org)")
