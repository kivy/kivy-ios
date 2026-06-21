"""Tests for kivy_ios/lock/resolver.py.

Covers pure helper functions, PipResolver (with _run_report monkeypatched),
_absorb edge cases, _run_report (with subprocess monkeypatched), and
get_resolver.  No network or real pip invocation is needed.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kivy_ios.lock.resolver import (
    PipResolver,
    ResolverError,
    _dep_names,
    _indent,
    abi_tags,
    get_resolver,
    pip_python_version,
    slice_suffixes,
    slice_tags,
)

# ---------------------------------------------------------------------------
# slice_tags
# ---------------------------------------------------------------------------


class TestSliceTags:
    def test_dots_replaced_with_underscores(self):
        tags = slice_tags("13.0")
        assert all("ios_13_0" in t for t in tags)

    def test_returns_three_slices(self):
        assert len(slice_tags("13.0")) == 3

    def test_slice_names(self):
        tags = slice_tags("16.0")
        assert "ios_16_0_arm64_iphoneos" in tags
        assert "ios_16_0_arm64_iphonesimulator" in tags
        assert "ios_16_0_x86_64_iphonesimulator" in tags

    def test_default_matches_explicit_both_archs(self):
        assert slice_tags("13.0") == slice_tags("13.0", ("arm64", "x86_64"))

    def test_arm64_only_drops_x86_64_slice(self):
        tags = slice_tags("13.0", ("arm64",))
        assert tags == (
            "ios_13_0_arm64_iphoneos",
            "ios_13_0_arm64_iphonesimulator",
        )
        assert not any("x86_64" in t for t in tags)

    def test_device_slice_always_present(self):
        # Even an x86_64-only simulator set still pins the arm64 device slice.
        tags = slice_tags("13.0", ("x86_64",))
        assert "ios_13_0_arm64_iphoneos" in tags
        assert "ios_13_0_x86_64_iphonesimulator" in tags
        assert "ios_13_0_arm64_iphonesimulator" not in tags

    def test_order_is_device_then_declared_simulator_archs(self):
        assert slice_tags("13.0", ("x86_64", "arm64")) == (
            "ios_13_0_arm64_iphoneos",
            "ios_13_0_x86_64_iphonesimulator",
            "ios_13_0_arm64_iphonesimulator",
        )


class TestSliceSuffixes:
    def test_default_is_device_plus_both_simulator_archs(self):
        assert slice_suffixes() == (
            "arm64_iphoneos",
            "arm64_iphonesimulator",
            "x86_64_iphonesimulator",
        )

    def test_arm64_only(self):
        assert slice_suffixes(("arm64",)) == (
            "arm64_iphoneos",
            "arm64_iphonesimulator",
        )


# ---------------------------------------------------------------------------
# pip_python_version
# ---------------------------------------------------------------------------


class TestPipPythonVersion:
    def test_plain_version_unchanged(self):
        assert pip_python_version("3.13") == "3.13"

    def test_three_part_version_truncated_to_two(self):
        assert pip_python_version("3.13.0") == "3.13"

    def test_prerelease_suffix_stripped(self):
        # "3.15.0a1" → digits of "0a1" = "0" → "3.15"
        assert pip_python_version("3.15.0a1") == "3.15"

    def test_dev_suffix_stripped(self):
        assert pip_python_version("3.15.0dev0") == "3.15"

    def test_single_component_returned_as_is(self):
        assert pip_python_version("3") == "3"

    def test_non_numeric_first_chunk_stops_early(self):
        # Edge case: chunk starts with non-digit → stops → falls back
        assert pip_python_version("abc") == "abc"


# ---------------------------------------------------------------------------
# abi_tags
# ---------------------------------------------------------------------------


class TestAbiTags:
    def test_returns_tuple(self):
        assert isinstance(abi_tags("3.13"), tuple)

    def test_first_tag_is_cpython(self):
        assert abi_tags("3.13")[0] == "cp313"

    def test_includes_abi3_and_none(self):
        tags = abi_tags("3.13")
        assert "abi3" in tags
        assert "none" in tags

    def test_prerelease_version(self):
        # "3.15.0a1" → join first two parts → "315"
        assert abi_tags("3.15.0a1")[0] == "cp315"


# ---------------------------------------------------------------------------
# _dep_names
# ---------------------------------------------------------------------------


class TestDepNames:
    def test_empty_list(self):
        assert _dep_names([]) == []

    def test_none_list(self):
        assert _dep_names(None) == []  # type: ignore[arg-type]

    def test_plain_name(self):
        assert _dep_names(["kivy"]) == ["kivy"]

    def test_version_specifier_stripped(self):
        assert _dep_names(["kivy>=3.0"]) == ["kivy"]

    def test_tilde_equal_specifier(self):
        assert _dep_names(["requests~=2.28"]) == ["requests"]

    def test_extras_stripped(self):
        assert _dep_names(["kivy[base]>=3.0"]) == ["kivy"]

    def test_marker_stripped(self):
        assert _dep_names(["kivy>=3.0; python_version>='3.10'"]) == ["kivy"]

    def test_multiple_packages(self):
        result = _dep_names(["kivy>=3.0", "more-itertools>=10"])
        assert result == ["kivy", "more-itertools"]

    def test_empty_string_skipped(self):
        assert _dep_names([""]) == []

    def test_parenthesised_specifier(self):
        assert _dep_names(["foo (>=1.0)"]) == ["foo"]


# ---------------------------------------------------------------------------
# _indent
# ---------------------------------------------------------------------------


class TestIndent:
    def test_single_line(self):
        assert _indent("hello") == "    hello"

    def test_multiline(self):
        result = _indent("line1\nline2")
        assert result == "    line1\n    line2"

    def test_empty_string_returns_empty(self):
        # "".splitlines() == [] → join yields ""
        assert _indent("") == ""

    def test_none_treated_as_empty(self):
        # (None or "") → "" → same as empty string
        assert _indent(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# get_resolver
# ---------------------------------------------------------------------------


class TestGetResolver:
    def test_pip_returns_pip_resolver(self):
        r = get_resolver("pip")
        assert isinstance(r, PipResolver)

    def test_unknown_backend_raises(self):
        with pytest.raises(ResolverError, match="unknown resolver backend"):
            get_resolver("uv")

    def test_custom_python_executable_forwarded(self):
        r = get_resolver("pip", python_executable="/usr/bin/python3")
        assert isinstance(r, PipResolver)
        assert r._python == "/usr/bin/python3"


# ---------------------------------------------------------------------------
# PipResolver.resolve — empty requirements fast path
# ---------------------------------------------------------------------------


class TestPipResolverEmpty:
    def test_empty_requirements_returns_empty_list(self):
        pr = PipResolver()
        result = pr.resolve(
            [],
            python_version="3.15.0",
            deployment_target="13.0",
            extra_index_urls=[],
        )
        assert result == []


# ---------------------------------------------------------------------------
# PipResolver._absorb — called directly with synthetic pip report items
# ---------------------------------------------------------------------------


def _wheel_item(
    name: str = "kivy",
    version: str = "3.0.0",
    filename: str = "kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl",
    sha256: str = "a" * 64,
) -> dict:
    url = f"https://files.pythonhosted.org/packages/aa/{filename}"
    return {
        "metadata": {
            "name": name,
            "version": version,
            "requires_python": ">=3.10",
            "requires_dist": [],
        },
        "download_info": {
            "url": url,
            "archive_info": {"hashes": {"sha256": sha256}},
        },
    }


class TestPipResolverAbsorb:
    def _absorb(self, item, merged=None, seen=None):
        pr = PipResolver()
        if merged is None:
            merged = {}
        if seen is None:
            seen = {}
        pr._absorb(item, merged, seen)
        return merged, seen

    def test_non_wheel_url_raises(self):
        item = _wheel_item(filename="kivy-3.0.0.tar.gz")
        item["download_info"]["url"] = "https://example.com/kivy-3.0.0.tar.gz"
        with pytest.raises(ResolverError, match="non-wheel source"):
            self._absorb(item)

    def test_new_package_added_to_merged(self):
        merged, _ = self._absorb(_wheel_item())
        assert "kivy" in merged
        assert merged["kivy"].version == "3.0.0"

    def test_wheel_added_to_package(self):
        merged, _ = self._absorb(_wheel_item())
        assert len(merged["kivy"].wheels) == 1

    def test_duplicate_filename_not_added_twice(self):
        item = _wheel_item()
        merged: dict = {}
        seen: dict = {}
        pr = PipResolver()
        pr._absorb(item, merged, seen)
        pr._absorb(item, merged, seen)  # same item again
        assert len(merged["kivy"].wheels) == 1

    def test_second_slice_wheel_appended(self):
        pr = PipResolver()
        merged: dict = {}
        seen: dict = {}
        item1 = _wheel_item(
            filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl"
        )
        item2 = _wheel_item(
            filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl"
        )
        pr._absorb(item1, merged, seen)
        pr._absorb(item2, merged, seen)
        assert len(merged["kivy"].wheels) == 2

    def test_version_mismatch_across_slices_raises(self):
        pr = PipResolver()
        merged: dict = {}
        seen: dict = {}
        device = _wheel_item(
            version="3.0.0",
            filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl",
        )
        sim = _wheel_item(
            version="3.0.1",
            filename="kivy-3.0.1-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl",
        )
        pr._absorb(device, merged, seen)
        with pytest.raises(ResolverError, match="inconsistent versions"):
            pr._absorb(sim, merged, seen)

    def test_matching_version_across_slices_ok(self):
        pr = PipResolver()
        merged: dict = {}
        seen: dict = {}
        device = _wheel_item(
            version="3.0.0",
            filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl",
        )
        sim = _wheel_item(
            version="3.0.0",
            filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl",
        )
        pr._absorb(device, merged, seen)
        pr._absorb(sim, merged, seen)
        assert merged["kivy"].version == "3.0.0"
        assert len(merged["kivy"].wheels) == 2

    def test_requires_python_captured(self):
        merged, _ = self._absorb(_wheel_item())
        assert merged["kivy"].requires_python == ">=3.10"

    def test_sha256_captured(self):
        merged, _ = self._absorb(_wheel_item(sha256="b" * 64))
        assert merged["kivy"].wheels[0].sha256 == "b" * 64

    def test_canonical_name_normalises_hyphens(self):
        item = _wheel_item(
            name="more-itertools", filename="more_itertools-10.5.0-py3-none-any.whl"
        )
        merged, _ = self._absorb(item)
        assert "more-itertools" in merged


# ---------------------------------------------------------------------------
# PipResolver._run_report — subprocess mocked
# ---------------------------------------------------------------------------


class TestPipResolverRunReport:
    def _make_report(self, install_items: list[dict]) -> dict:
        return {"install": install_items, "environment": {}}

    def test_success_returns_parsed_json(self, tmp_path, monkeypatch):
        report_data = self._make_report([])

        def fake_run(cmd, **kw):
            # Write the report file that _run_report expects.
            report_path = Path(next(a for a in cmd if a.endswith("report.json")))
            report_path.write_text(json.dumps(report_data))
            result = MagicMock()
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", fake_run)
        pr = PipResolver()
        result = pr._run_report(
            ["kivy"],
            python_version="3.15.0",
            platform_tag="ios_13_0_arm64_iphoneos",
            abis=("cp315", "abi3", "none"),
            extra_index_urls=[],
            find_links=[],
            offline=False,
        )
        assert result == report_data

    def test_nonzero_returncode_raises(self, monkeypatch):
        def fake_run(cmd, **kw):
            result = MagicMock()
            result.returncode = 1
            result.stderr = "ERROR: no matching distribution found"
            result.stdout = ""
            return result

        monkeypatch.setattr(subprocess, "run", fake_run)
        pr = PipResolver()
        with pytest.raises(ResolverError, match="pip could not resolve"):
            pr._run_report(
                ["bad-pkg"],
                python_version="3.15.0",
                platform_tag="ios_13_0_arm64_iphoneos",
                abis=("cp315",),
                extra_index_urls=[],
                find_links=[],
                offline=False,
            )

    def test_json_parse_error_raises(self, monkeypatch):
        def fake_run(cmd, **kw):
            # Write invalid JSON to the report file.
            report_path = Path(next(a for a in cmd if a.endswith("report.json")))
            report_path.write_text("not valid json {{")
            result = MagicMock()
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", fake_run)
        pr = PipResolver()
        with pytest.raises(ResolverError, match="could not read pip report"):
            pr._run_report(
                ["kivy"],
                python_version="3.15.0",
                platform_tag="ios_13_0_arm64_iphoneos",
                abis=("cp315",),
                extra_index_urls=[],
                find_links=[],
                offline=False,
            )

    def test_offline_adds_no_index_flag(self, monkeypatch):
        captured: list[list[str]] = []

        def fake_run(cmd, **kw):
            captured.append(list(cmd))
            report_path = Path(next(a for a in cmd if a.endswith("report.json")))
            report_path.write_text(json.dumps({"install": []}))
            result = MagicMock()
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", fake_run)
        pr = PipResolver()
        pr._run_report(
            ["kivy"],
            python_version="3.15.0",
            platform_tag="ios_13_0_arm64_iphoneos",
            abis=("cp315",),
            extra_index_urls=[],
            find_links=[],
            offline=True,
        )
        assert "--no-index" in captured[0]

    def test_find_links_added_to_command(self, monkeypatch):
        captured: list[list[str]] = []

        def fake_run(cmd, **kw):
            captured.append(list(cmd))
            report_path = Path(next(a for a in cmd if a.endswith("report.json")))
            report_path.write_text(json.dumps({"install": []}))
            result = MagicMock()
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", fake_run)
        pr = PipResolver()
        pr._run_report(
            ["kivy"],
            python_version="3.15.0",
            platform_tag="ios_13_0_arm64_iphoneos",
            abis=("cp315",),
            extra_index_urls=[],
            find_links=["/wheels"],
            offline=False,
        )
        assert "--find-links" in captured[0]
        idx = captured[0].index("--find-links")
        assert captured[0][idx + 1] == "/wheels"

    def test_extra_index_url_added(self, monkeypatch):
        captured: list[list[str]] = []

        def fake_run(cmd, **kw):
            captured.append(list(cmd))
            report_path = Path(next(a for a in cmd if a.endswith("report.json")))
            report_path.write_text(json.dumps({"install": []}))
            result = MagicMock()
            result.returncode = 0
            return result

        monkeypatch.setattr(subprocess, "run", fake_run)
        pr = PipResolver()
        pr._run_report(
            ["kivy"],
            python_version="3.15.0",
            platform_tag="ios_13_0_arm64_iphoneos",
            abis=("cp315",),
            extra_index_urls=["https://custom.index/simple"],
            find_links=[],
            offline=False,
        )
        assert "--extra-index-url" in captured[0]


# ---------------------------------------------------------------------------
# PipResolver.resolve — end-to-end with _run_report mocked
# ---------------------------------------------------------------------------


class TestPipResolverResolve:
    def _fake_run_report(self, wheel_items_per_slice: list[list[dict]]):
        """Return a _run_report side-effect that yields items for each slice."""
        calls = iter(wheel_items_per_slice)

        def _impl(self_inner, requirements, **kwargs):
            try:
                items = next(calls)
            except StopIteration:
                items = []
            return {"install": items}

        return _impl

    def test_empty_requirements_no_subprocess(self, monkeypatch):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("subprocess called")),
        )
        pr = PipResolver()
        assert (
            pr.resolve(
                [],
                python_version="3.15.0",
                deployment_target="13.0",
                extra_index_urls=[],
            )
            == []
        )

    def test_resolve_merges_three_slices(self, monkeypatch):
        slice_items = [
            [
                _wheel_item(
                    filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl"
                )
            ],
            [
                _wheel_item(
                    filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl"
                )
            ],
            [
                _wheel_item(
                    filename="kivy-3.0.0-cp315-cp315-ios_13_0_x86_64_iphonesimulator.whl"
                )
            ],
        ]
        call_iter = iter(slice_items)

        def fake_run_report(
            self_inner,
            requirements,
            *,
            python_version,
            platform_tag,
            abis,
            extra_index_urls,
            find_links,
            offline,
        ):
            return {"install": next(call_iter)}

        monkeypatch.setattr(PipResolver, "_run_report", fake_run_report)
        pr = PipResolver()
        packages = pr.resolve(
            ["kivy>=3.0"],
            python_version="3.15.0",
            deployment_target="13.0",
            extra_index_urls=[],
        )
        assert len(packages) == 1
        assert packages[0].name == "kivy"
        assert len(packages[0].wheels) == 3

    def test_resolve_returns_multiple_packages(self, monkeypatch):
        kivy_whl = _wheel_item(
            filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl"
        )
        mi_whl = _wheel_item(
            name="more-itertools",
            version="10.5.0",
            filename="more_itertools-10.5.0-py3-none-any.whl",
        )
        call_iter = iter([[kivy_whl, mi_whl]] * 3)

        def fake_run_report(
            self_inner,
            requirements,
            *,
            python_version,
            platform_tag,
            abis,
            extra_index_urls,
            find_links,
            offline,
        ):
            return {"install": next(call_iter)}

        monkeypatch.setattr(PipResolver, "_run_report", fake_run_report)
        pr = PipResolver()
        packages = pr.resolve(
            ["kivy", "more-itertools"],
            python_version="3.15.0",
            deployment_target="13.0",
            extra_index_urls=[],
        )
        names = {p.name for p in packages}
        assert "kivy" in names
        assert "more-itertools" in names

    def test_resolve_raises_on_version_mismatch_between_slices(self, monkeypatch):
        # Device slice resolves kivy 3.0.0; a later simulator slice resolves
        # 3.0.1 for the same requirement (e.g. one slice was not published for
        # 3.0.1 upstream). The merge must fail loudly, not silently mix wheels.
        slice_items = [
            [
                _wheel_item(
                    version="3.0.0",
                    filename="kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl",
                )
            ],
            [
                _wheel_item(
                    version="3.0.1",
                    filename="kivy-3.0.1-cp315-cp315-ios_13_0_arm64_iphonesimulator.whl",
                )
            ],
        ]
        call_iter = iter(slice_items)

        def fake_run_report(
            self_inner,
            requirements,
            *,
            python_version,
            platform_tag,
            abis,
            extra_index_urls,
            find_links,
            offline,
        ):
            return {"install": next(call_iter, [])}

        monkeypatch.setattr(PipResolver, "_run_report", fake_run_report)
        pr = PipResolver()
        with pytest.raises(ResolverError, match="inconsistent versions"):
            pr.resolve(
                ["kivy>=3.0"],
                python_version="3.15.0",
                deployment_target="13.0",
                extra_index_urls=[],
            )
