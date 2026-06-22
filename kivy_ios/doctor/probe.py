"""Environment probes for doctor (the only place that touches the host).

``Probe`` is the protocol the checks depend on; ``RealProbe`` is the macOS
implementation (subprocess/socket/Mach-O parsing). Unit tests supply a fake
object with the same methods, so the check logic never shells out.
"""

from __future__ import annotations

import socket
import struct
import subprocess
from pathlib import Path
from typing import Protocol

# Mach-O platform constants (LC_BUILD_VERSION `platform`).
PLATFORM_NAMES = {
    1: "macos",
    2: "ios",
    3: "tvos",
    4: "watchos",
    7: "ios-simulator",
    8: "tvos-simulator",
    9: "watchos-simulator",
}
LC_BUILD_VERSION = 0x32
_MACHO_MAGICS = {0xFEEDFACE, 0xFEEDFACF, 0xCEFAEDFE, 0xCFFAEDFE}


class Probe(Protocol):
    def xcode_version(self) -> str | None: ...
    def xcode_select_path(self) -> str | None: ...
    def has_xcrun_clang(self) -> bool: ...
    def has_swift_toolchain(self) -> bool: ...
    def simulator_runtimes(self) -> list[str]: ...
    def latest_toolchain_version(self) -> str | None: ...
    def keychain_identities(self) -> list[str]: ...
    def tcp_reachable(self, host: str, port: int) -> bool: ...
    def binary_platforms(self, path: Path) -> set[str]: ...


class RealProbe:
    def xcode_version(self) -> str | None:
        out = _capture(["xcodebuild", "-version"])
        if not out:
            return None
        first = out.splitlines()[0]
        return first.replace("Xcode", "").strip() or None

    def xcode_select_path(self) -> str | None:
        return _capture(["xcode-select", "-p"]) or None

    def has_xcrun_clang(self) -> bool:
        return bool(_capture(["xcrun", "--find", "clang"]))

    def has_swift_toolchain(self) -> bool:
        return bool(_capture(["xcrun", "--find", "swift"]))

    def simulator_runtimes(self) -> list[str]:
        out = _capture(["xcrun", "simctl", "list", "runtimes", "iOS"])
        versions = []
        for line in out.splitlines():
            # "iOS 18.0 (...) - com.apple.CoreSimulator.SimRuntime.iOS-18-0"
            line = line.strip()
            if line.startswith("iOS "):
                parts = line.split()
                if len(parts) >= 2:
                    versions.append(parts[1])
        return versions

    def latest_toolchain_version(self) -> str | None:
        # Best-effort PyPI lookup; failures are non-fatal.
        try:
            import json
            import urllib.request

            url = "https://pypi.org/pypi/kivy-ios/json"
            with urllib.request.urlopen(url, timeout=3) as resp:  # noqa: S310
                data = json.load(resp)
            return data.get("info", {}).get("version")
        except Exception:
            return None

    def keychain_identities(self) -> list[str]:
        out = _capture(["security", "find-identity", "-v", "-p", "codesigning"])
        return [line.strip() for line in out.splitlines() if line.strip()]

    def tcp_reachable(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except OSError:
            return False

    def binary_platforms(self, path: Path) -> set[str]:
        """Return the set of OS platforms a Mach-O (or fat) binary targets."""
        try:
            data = path.read_bytes()
        except OSError:
            return set()
        return _macho_platforms(data)


def _capture(argv: list[str]) -> str:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True)
    except (OSError, ValueError):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def _macho_platforms(data: bytes) -> set[str]:
    if len(data) < 4:
        return set()
    magic = struct.unpack(">I", data[:4])[0]
    # Fat binary: parse each arch slice.
    if magic in (0xCAFEBABE, 0xBEBAFECA):
        platforms: set[str] = set()
        nfat = struct.unpack(">I", data[4:8])[0]
        for i in range(nfat):
            off = 8 + i * 20
            (offset,) = struct.unpack(">I", data[off + 8 : off + 12])
            platforms |= _thin_platforms(data[offset:])
        return platforms
    return _thin_platforms(data)


def _thin_platforms(data: bytes) -> set[str]:
    if len(data) < 4:
        return set()
    magic = struct.unpack(">I", data[:4])[0]
    if magic not in _MACHO_MAGICS:
        return set()
    little = magic in (0xCEFAEDFE, 0xCFFAEDFE)
    is64 = magic in (0xFEEDFACF, 0xCFFAEDFE)
    end = "<" if little else ">"
    header = 32 if is64 else 28
    ncmds = struct.unpack(end + "I", data[16:20])[0]
    offset = header
    platforms: set[str] = set()
    for _ in range(ncmds):
        if offset + 8 > len(data):
            break
        cmd, cmdsize = struct.unpack(end + "II", data[offset : offset + 8])
        if cmd == LC_BUILD_VERSION and offset + 16 <= len(data):
            (plat,) = struct.unpack(end + "I", data[offset + 8 : offset + 12])
            platforms.add(PLATFORM_NAMES.get(plat, f"platform-{plat}"))
        if cmdsize == 0:
            break
        offset += cmdsize
    return platforms
