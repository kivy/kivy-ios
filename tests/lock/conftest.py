"""Hermetic fakes for lock tests: no network, no pip subprocess."""

from __future__ import annotations

import textwrap

import pytest

from kivy_ios.lock.python_meta import PythonXcframeworkInfo
from kivy_ios.lock.resolver import ResolvedPackage, ResolvedWheel, slice_tags
from kivy_ios.lock.spm import ResolvedSwiftPackage


class FakeResolver:
    """Deterministic resolver: kivy (compiled, 3 slices) + a pure-Python dep."""

    def __init__(self, *, drop_slice: str | None = None) -> None:
        self.calls: list[dict] = []
        self._drop_slice = drop_slice

    def resolve(
        self,
        requirements,
        *,
        python_version,
        deployment_target,
        extra_index_urls,
        find_links=None,
        offline=False,
        simulator_archs=None,
    ):
        self.calls.append(
            {
                "requirements": list(requirements),
                "python_version": python_version,
                "deployment_target": deployment_target,
                "extra_index_urls": list(extra_index_urls),
                "find_links": list(find_links or []),
                "offline": offline,
                "simulator_archs": simulator_archs,
            }
        )
        if not requirements:
            return []
        tags = slice_tags(deployment_target, simulator_archs)
        abi = "cp" + "".join(python_version.split(".")[:2])
        kivy_wheels = []
        for tag in tags:
            if tag == self._drop_slice:
                continue
            fname = f"kivy-3.0.0-{abi}-{abi}-{tag}.whl"
            kivy_wheels.append(
                ResolvedWheel(
                    filename=fname,
                    url=f"https://files.pythonhosted.org/packages/aa/{fname}",
                    sha256="a" * 64,
                )
            )
        kivy = ResolvedPackage(
            name="kivy",
            version="3.0.0",
            wheels=kivy_wheels,
            requires_python=">=3.10",
            dependencies=["more-itertools"],
        )
        mi = ResolvedPackage(
            name="more-itertools",
            version="10.5.0",
            wheels=[
                ResolvedWheel(
                    filename="more_itertools-10.5.0-py3-none-any.whl",
                    url="https://files.pythonhosted.org/packages/bb/more_itertools-10.5.0-py3-none-any.whl",
                    sha256="b" * 64,
                )
            ],
            requires_python=">=3.8",
        )
        return [kivy, mi]


class FakePythonProvider:
    def __init__(self, *, floor: str = "13.0") -> None:
        self._floor = floor

    def get(self, version: str, *, offline: bool = False) -> PythonXcframeworkInfo:
        return PythonXcframeworkInfo(
            version=version,
            url=f"https://www.python.org/ftp/python/{version}/python-{version}-iOS-XCframework.tar.gz",
            sha256="c" * 64,
            ios_floor=self._floor,
        )


class FakeSpmResolver:
    """Deterministic SPM resolver: pins each remote package to a fake revision."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def resolve(self, packages, *, project_root, offline=False):
        self.calls.append(
            {
                "names": [p.name for p in packages],
                "project_root": project_root,
                "offline": offline,
            }
        )
        out = []
        for i, pkg in enumerate(packages):
            # Only remote packages reach the resolver.
            out.append(
                ResolvedSwiftPackage(
                    name=pkg.name,
                    revision=f"{i:x}" * 40,
                    version="9.9.9",
                )
            )
        return out


@pytest.fixture
def fake_resolver():
    return FakeResolver()


@pytest.fixture
def fake_spm_resolver():
    return FakeSpmResolver()


@pytest.fixture
def fake_python_provider():
    return FakePythonProvider()


@pytest.fixture
def minimal_pyproject() -> str:
    return textwrap.dedent(
        """
        [project]
        name = "myapp"
        version = "1.0.0"
        requires-python = ">=3.15"
        dependencies = ["kivy>=3.0,<4", "more-itertools>=10.5"]

        [tool.kivy]
        app_dir = "src"

        [tool.kivy.ios]
        schema_version = 1
        bundle_id = "org.example.myapp"
        deployment_target = "13.0"

        [tool.kivy.ios.python]
        version = "3.15.0"
        """
    ).strip()
