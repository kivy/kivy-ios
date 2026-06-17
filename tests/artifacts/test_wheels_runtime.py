"""Phase 4 — wheel slice selection, pip command, runtime adapters."""

from __future__ import annotations

import pytest

from kivy_ios.artifacts.runtime import (
    BeewareRuntime,
    PythonOrgRuntime,
    get_runtime,
)
from kivy_ios.artifacts.wheels import (
    BuildSlice,
    WheelSelectionError,
    pip_install_command,
    select_wheel,
)
from kivy_ios.lock.model import LockedPackage, LockedWheel


def _compiled_pkg():
    return LockedPackage(
        name="kivy",
        version="3.0.0",
        wheels=tuple(
            LockedWheel(
                name=f"kivy-3.0.0-cp315-cp315-{tag}.whl",
                url="https://e/" + tag,
                sha256="a" * 64,
            )
            for tag in (
                "ios_13_0_arm64_iphoneos",
                "ios_13_0_arm64_iphonesimulator",
                "ios_13_0_x86_64_iphonesimulator",
            )
        ),
    )


def _pure_pkg():
    return LockedPackage(
        name="more-itertools",
        version="10.5.0",
        wheels=(
            LockedWheel(
                name="more_itertools-10.5.0-py3-none-any.whl",
                url="https://e/mi",
                sha256="b" * 64,
            ),
        ),
    )


class TestSliceSelection:
    @pytest.mark.parametrize(
        "target,arch,expected",
        [
            ("device", "arm64", "ios_13_0_arm64_iphoneos"),
            ("simulator", "arm64", "ios_13_0_arm64_iphonesimulator"),
            ("simulator", "x86_64", "ios_13_0_x86_64_iphonesimulator"),
        ],
    )
    def test_selects_matching_slice(self, target, arch, expected):
        slice_ = BuildSlice(target=target, arch=arch, deployment_target="13.0")
        assert slice_.platform_tag == expected
        wheel = select_wheel(_compiled_pkg(), slice_)
        assert wheel.platform_tag == expected

    def test_pure_python_matches_any_slice(self):
        slice_ = BuildSlice(target="device", arch="arm64", deployment_target="13.0")
        wheel = select_wheel(_pure_pkg(), slice_)
        assert wheel.is_pure_python

    def test_ios13_wheel_compatible_with_16_target(self):
        """ios_13_0 wheels are valid for a deployment_target=16.0 project."""
        slice_ = BuildSlice(target="device", arch="arm64", deployment_target="16.0")
        wheel = select_wheel(_compiled_pkg(), slice_)
        assert wheel.platform_tag == "ios_13_0_arm64_iphoneos"

    def test_prefers_highest_compatible_version(self):
        """When both ios_13_0 and ios_16_0 are available for 16.0 target, prefer 16.0."""
        pkg = LockedPackage(
            name="kivy",
            version="3.0.0",
            wheels=(
                LockedWheel(
                    name="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl",
                    url="https://e/13",
                    sha256="a" * 64,
                ),
                LockedWheel(
                    name="kivy-3.0.0-cp315-cp315-ios_16_0_arm64_iphoneos.whl",
                    url="https://e/16",
                    sha256="b" * 64,
                ),
            ),
        )
        slice_ = BuildSlice(target="device", arch="arm64", deployment_target="16.0")
        wheel = select_wheel(pkg, slice_)
        assert wheel.platform_tag == "ios_16_0_arm64_iphoneos"

    def test_rejects_wheel_higher_than_target(self):
        """ios_16_0 wheel is not compatible with deployment_target=13.0."""
        pkg = LockedPackage(
            name="x",
            version="1",
            wheels=(
                LockedWheel(
                    name="x-1-cp315-cp315-ios_16_0_arm64_iphoneos.whl",
                    url="https://e/x",
                    sha256="c" * 64,
                ),
            ),
        )
        slice_ = BuildSlice(target="device", arch="arm64", deployment_target="13.0")
        with pytest.raises(WheelSelectionError):
            select_wheel(pkg, slice_)

    def test_missing_slice_raises(self):
        pkg = LockedPackage(
            name="x",
            version="1",
            wheels=(
                LockedWheel(
                    name="x-1-cp315-cp315-ios_13_0_arm64_iphoneos.whl",
                    url="https://e/x",
                    sha256="c" * 64,
                ),
            ),
        )
        slice_ = BuildSlice(target="simulator", arch="x86_64", deployment_target="13.0")
        with pytest.raises(WheelSelectionError):
            select_wheel(pkg, slice_)


class TestPipCommand:
    def test_command_has_cross_install_flags(self):
        cmd = pip_install_command(
            ["/tmp/kivy.whl"],
            target_dir="pip-deps",
            platform_tag="ios_13_0_arm64_iphoneos",
            python_version="3.15",
            abi="cp315",
            python_executable="/usr/bin/python3",
        )
        assert "--no-deps" in cmd
        assert "--only-binary=:all:" in cmd
        assert "ios_13_0_arm64_iphoneos" in cmd
        assert cmd[-1] == "/tmp/kivy.whl"
        assert "--target" in cmd and "pip-deps" in cmd


class TestRuntimes:
    def test_python_org_url_and_invocation(self):
        rt = PythonOrgRuntime()
        art = rt.xcframework_artifact("3.15.0")
        assert art.url == (
            "https://www.python.org/ftp/python/3.15.0/"
            "python-3.15.0-iOS-XCframework.tar.gz"
        )
        assert (
            rt.build_python_invocation(
                xcframework="Python.xcframework", app="app", pip_deps="pip-deps"
            )
            == "install_python Python.xcframework app pip-deps"
        )
        assert rt.ios_floor("3.15.0") == "13.0"

    def test_beeware_url(self):
        rt = BeewareRuntime(build="b5")
        art = rt.xcframework_artifact("3.13.2")
        assert "Python-3.13-iOS-support.b5.tar.gz" in art.url
        assert "github.com/beeware/Python-Apple-support" in art.url

    def test_get_runtime_factory(self):
        assert get_runtime("python.org").name == "python.org"
        assert get_runtime("beeware").name == "beeware"
        with pytest.raises(ValueError):
            get_runtime("nonsense")
