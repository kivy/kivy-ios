"""Tests for RealProbe methods and Mach-O binary parsing helpers."""

from __future__ import annotations

import socket
import struct
import subprocess
import sys
from unittest.mock import MagicMock, patch

# Stub heavy optional deps so this module can be collected without the full
# Xcode / pbxproj tool-chain installed (CI has them; local dev may not).
if "pbxproj" not in sys.modules:
    _pbx = MagicMock()
    sys.modules["pbxproj"] = _pbx
    sys.modules["pbxproj.pbxextensions"] = _pbx
    sys.modules["pbxproj.pbxextensions.ProjectFiles"] = _pbx

from kivy_ios.doctor.probe import (  # noqa: E402
    LC_BUILD_VERSION,
    PLATFORM_NAMES,
    RealProbe,
    _capture,
    _macho_platforms,
    _thin_platforms,
)

# ---------------------------------------------------------------------------
# Mach-O binary builder helpers
# ---------------------------------------------------------------------------


def _make_thin_macho(
    platform: int,
    *,
    little: bool = True,
    is64: bool = True,
    add_lc_build_version: bool = True,
) -> bytes:
    """Build a minimal Mach-O binary with one optional LC_BUILD_VERSION.

    Mach-O magic constants are the *real* values (MH_MAGIC_64 = 0xFEEDFACF,
    MH_MAGIC = 0xFEEDFACE) packed in the file's own endianness.  When the
    probe code reads them back with big-endian ``struct.unpack(">I", ...)`` it
    sees 0xCFFAEDFE / 0xCEFAEDFE for little-endian files and 0xFEEDFACF /
    0xFEEDFACE for big-endian files — exactly what ``_thin_platforms`` checks.
    """
    end = "<" if little else ">"

    # Real Mach-O magic values (stored in native byte order).
    if is64:
        magic = 0xFEEDFACF  # MH_MAGIC_64
    else:
        magic = 0xFEEDFACE  # MH_MAGIC

    lc_payload = b""
    if add_lc_build_version:
        lc_payload = struct.pack(
            end + "IIIIII",
            LC_BUILD_VERSION,  # cmd
            24,  # cmdsize
            platform,  # platform
            0x000D0000,  # minos (13.0)
            0,  # sdk
            0,  # ntools
        )

    ncmds = 1 if lc_payload else 0
    sizeofcmds = len(lc_payload)

    if is64:
        header = struct.pack(
            end + "IIIIIIII",
            magic,
            0x0100000C,  # cputype ARM64
            0,  # cpusubtype
            2,  # filetype MH_EXECUTE
            ncmds,
            sizeofcmds,
            0,  # flags
            0,  # reserved
        )
    else:
        header = struct.pack(
            end + "IIIIIII",
            magic,
            12,  # cputype ARM
            0,  # cpusubtype
            2,  # filetype
            ncmds,
            sizeofcmds,
            0,  # flags
        )

    return header + lc_payload


def _make_fat_macho(*slices: bytes) -> bytes:
    """Wrap one or more thin Mach-O slices in a fat binary header."""
    nfat = len(slices)
    # Fat header: magic(4) + nfat(4) + nfat * arch_entry(20)
    header_size = 8 + nfat * 20
    offsets: list[int] = []
    current = header_size
    for s in slices:
        offsets.append(current)
        current += len(s)

    header = struct.pack(">II", 0xCAFEBABE, nfat)
    for i, s in enumerate(slices):
        # arch entry: cputype, cpusubtype, offset, size, align
        header += struct.pack(">IIIII", 0x0100000C, 0, offsets[i], len(s), 0)

    return header + b"".join(slices)


# ---------------------------------------------------------------------------
# _thin_platforms
# ---------------------------------------------------------------------------


class TestThinPlatforms:
    def test_too_short_returns_empty(self):
        assert _thin_platforms(b"\x00\x01") == set()

    def test_non_macho_magic_returns_empty(self):
        assert _thin_platforms(b"\xde\xad\xbe\xef") == set()

    def test_ios_little_endian_64bit(self):
        data = _make_thin_macho(2, little=True, is64=True)  # 2 = ios
        assert _thin_platforms(data) == {"ios"}

    def test_ios_simulator_little_endian_32bit(self):
        data = _make_thin_macho(7, little=True, is64=False)  # 7 = ios-simulator
        assert _thin_platforms(data) == {"ios-simulator"}

    def test_macos_big_endian_64bit(self):
        data = _make_thin_macho(1, little=False, is64=True)  # 1 = macos
        assert _thin_platforms(data) == {"macos"}

    def test_macos_big_endian_32bit(self):
        data = _make_thin_macho(1, little=False, is64=False)
        assert _thin_platforms(data) == {"macos"}

    def test_unknown_platform_fallback(self):
        data = _make_thin_macho(99, little=True, is64=True)
        result = _thin_platforms(data)
        assert result == {"platform-99"}
        assert 99 not in PLATFORM_NAMES

    def test_no_lc_build_version_returns_empty(self):
        data = _make_thin_macho(2, add_lc_build_version=False)
        assert _thin_platforms(data) == set()

    def test_truncated_after_header_breaks_early(self):
        # ncmds says 5 but no load command bytes follow the header
        end = "<"
        magic = 0xCFFAEDFE
        header = struct.pack(
            end + "IIIIIIII",
            magic,
            0x0100000C,  # cputype
            0,  # cpusubtype
            2,  # filetype
            5,  # ncmds — but no LC data follows
            0,  # sizeofcmds
            0,  # flags
            0,  # reserved
        )
        # The header alone is 32 bytes; offset+8 > len(data) fires immediately.
        assert _thin_platforms(header) == set()

    def test_zero_cmdsize_breaks_loop(self):
        # A load command with cmdsize=0 must terminate the loop.
        end = "<"
        magic = 0xCFFAEDFE
        lc = struct.pack(end + "II", 0x00, 0)  # cmd=0, cmdsize=0
        header = struct.pack(
            end + "IIIIIIII",
            magic,
            0x0100000C,
            0,
            2,
            1,  # ncmds
            len(lc),
            0,
            0,
        )
        assert _thin_platforms(header + lc) == set()


# ---------------------------------------------------------------------------
# _macho_platforms
# ---------------------------------------------------------------------------


class TestMachoPlatforms:
    def test_too_short_returns_empty(self):
        assert _macho_platforms(b"\x00") == set()

    def test_non_fat_non_macho_returns_empty(self):
        assert _macho_platforms(b"\x00\x01\x02\x03") == set()

    def test_thin_binary_direct(self):
        data = _make_thin_macho(2)
        assert _macho_platforms(data) == {"ios"}

    def test_fat_binary_single_slice(self):
        fat = _make_fat_macho(_make_thin_macho(2))
        assert _macho_platforms(fat) == {"ios"}

    def test_fat_binary_multiple_slices(self):
        fat = _make_fat_macho(_make_thin_macho(2), _make_thin_macho(7))
        assert _macho_platforms(fat) == {"ios", "ios-simulator"}


# ---------------------------------------------------------------------------
# _capture
# ---------------------------------------------------------------------------


class TestCapture:
    def test_success_returns_stdout(self, monkeypatch):
        result = MagicMock()
        result.returncode = 0
        result.stdout = "hello\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: result)
        assert _capture(["echo", "hello"]) == "hello\n"

    def test_nonzero_returncode_returns_empty(self, monkeypatch):
        result = MagicMock()
        result.returncode = 1
        result.stdout = "ignored"
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: result)
        assert _capture(["false"]) == ""

    def test_oserror_returns_empty(self, monkeypatch):
        def raise_os(*a, **k):
            raise OSError("not found")

        monkeypatch.setattr(subprocess, "run", raise_os)
        assert _capture(["nonexistent-command"]) == ""

    def test_valueerror_returns_empty(self, monkeypatch):
        def raise_val(*a, **k):
            raise ValueError("bad")

        monkeypatch.setattr(subprocess, "run", raise_val)
        assert _capture(["bad"]) == ""


# ---------------------------------------------------------------------------
# RealProbe methods
# ---------------------------------------------------------------------------


class TestRealProbe:
    def _probe(self) -> RealProbe:
        return RealProbe()

    # --- xcode_version ---

    def test_xcode_version_parses_output(self, monkeypatch):
        monkeypatch.setattr(
            "kivy_ios.doctor.probe._capture",
            lambda _: "Xcode 16.0\nBuild version 16A242d\n",
        )
        assert self._probe().xcode_version() == "16.0"

    def test_xcode_version_empty_returns_none(self, monkeypatch):
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: "")
        assert self._probe().xcode_version() is None

    # --- pip_version ---

    def test_pip_version_parses_output(self, monkeypatch):
        monkeypatch.setattr(
            "kivy_ios.doctor.probe._capture",
            lambda _: "pip 24.3.1 from /x/site-packages/pip (python 3.15)\n",
        )
        assert self._probe().pip_version() == "24.3.1"

    def test_pip_version_unavailable_returns_none(self, monkeypatch):
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: "")
        assert self._probe().pip_version() is None

    # --- xcode_select_path ---

    def test_xcode_select_path_returns_value(self, monkeypatch):
        monkeypatch.setattr(
            "kivy_ios.doctor.probe._capture",
            lambda _: "/Applications/Xcode.app/Contents/Developer\n",
        )
        result = self._probe().xcode_select_path()
        assert result == "/Applications/Xcode.app/Contents/Developer\n"

    def test_xcode_select_path_empty_returns_none(self, monkeypatch):
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: "")
        assert self._probe().xcode_select_path() is None

    # --- has_xcrun_clang ---

    def test_has_xcrun_clang_true(self, monkeypatch):
        monkeypatch.setattr(
            "kivy_ios.doctor.probe._capture", lambda _: "/usr/bin/clang"
        )
        assert self._probe().has_xcrun_clang() is True

    def test_has_xcrun_clang_false(self, monkeypatch):
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: "")
        assert self._probe().has_xcrun_clang() is False

    # --- simulator_runtimes ---

    def test_simulator_runtimes_parses_ios_lines(self, monkeypatch):
        output = (
            "== Runtimes ==\n"
            "iOS 17.5 (17.5 - 21F79) - com.apple.CoreSimulator.SimRuntime.iOS-17-5\n"
            "iOS 18.0 (18.0 - 22A3351) - com.apple.CoreSimulator.SimRuntime.iOS-18-0\n"
            "watchOS 11.0 (11.0 - 22R5339b) - ignored\n"
        )
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: output)
        assert self._probe().simulator_runtimes() == ["17.5", "18.0"]

    def test_simulator_runtimes_empty_output(self, monkeypatch):
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: "")
        assert self._probe().simulator_runtimes() == []

    # --- keychain_identities ---

    def test_keychain_identities_parses_lines(self, monkeypatch):
        output = (
            '  1) ABC123 "Apple Development: Test"\n  2) DEF456 "iPhone Distribution"\n'
        )
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: output)
        ids = self._probe().keychain_identities()
        assert len(ids) == 2
        assert ids[0].startswith("1)")

    def test_keychain_identities_empty(self, monkeypatch):
        monkeypatch.setattr("kivy_ios.doctor.probe._capture", lambda _: "")
        assert self._probe().keychain_identities() == []

    # --- tcp_reachable ---

    def test_tcp_reachable_success(self, monkeypatch):
        cm = MagicMock()
        cm.__enter__ = lambda s: s
        cm.__exit__ = lambda s, *a: None
        monkeypatch.setattr(socket, "create_connection", lambda *a, **k: cm)
        assert self._probe().tcp_reachable("pypi.org", 443) is True

    def test_tcp_reachable_oserror(self, monkeypatch):
        def raise_os(*a, **k):
            raise OSError("connection refused")

        monkeypatch.setattr(socket, "create_connection", raise_os)
        assert self._probe().tcp_reachable("pypi.org", 443) is False

    # --- binary_platforms ---

    def test_binary_platforms_missing_file_returns_empty(self, tmp_path):
        assert self._probe().binary_platforms(tmp_path / "nonexistent.dylib") == set()

    def test_binary_platforms_valid_macho(self, tmp_path):
        binary = tmp_path / "test.dylib"
        binary.write_bytes(_make_thin_macho(2))  # ios
        assert self._probe().binary_platforms(binary) == {"ios"}

    # --- latest_toolchain_version ---

    def test_latest_toolchain_version_success(self):
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda s, *a: None

        with patch("urllib.request.urlopen", return_value=fake_resp):
            with patch("json.load", return_value={"info": {"version": "3.1.0"}}):
                result = self._probe().latest_toolchain_version()
        assert result == "3.1.0"

    def test_latest_toolchain_version_network_error(self):
        with patch("urllib.request.urlopen", side_effect=OSError("network")):
            assert self._probe().latest_toolchain_version() is None
