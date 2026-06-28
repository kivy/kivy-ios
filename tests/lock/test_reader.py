"""Phase 2/3 — pylock.ios.toml reader robustness (spec 02).

`toolchain lock` is the writer, so the reader only needs to fail cleanly on a
missing, corrupt, hand-edited, or future-schema file — never leak a raw
KeyError/TypeError.
"""

from __future__ import annotations

import pytest

from kivy_ios.lock.reader import LockError, loads

# A minimal, valid lockfile body that every corruption test mutates.
VALID = """\
lock-version = "1.0"
created-by = "kivy-ios"
requires-python = ">=3.15"

[[packages]]
name = "kivy"
version = "3.0.0"

[[packages.wheels]]
name = "kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl"
url = "https://example.com/kivy.whl"
hashes = { sha256 = "aa" }

[tool.kivy_ios]
schema_version = 1
toolchain_version = "3.0.0"
generated_at = "2026-05-27T00:00:00Z"
pyproject_sha256 = "deadbeef"
tool_kivy_ios_schema_version = 1

[tool.kivy_ios.python_xcframework]
version = "3.15.0"
url = "https://example.com/python.tar.gz"
sha256 = "cc"
"""


class TestValidBaseline:
    def test_parses(self):
        lock = loads(VALID)
        assert lock.python_xcframework.version == "3.15.0"
        assert lock.packages[0].name == "kivy"
        assert lock.schema_version == 1


class TestCorruption:
    def test_invalid_toml(self):
        with pytest.raises(LockError, match="not valid TOML"):
            loads("lock-version = \n")

    def test_missing_tool_table(self):
        with pytest.raises(LockError, match=r"missing the \[tool.kivy_ios\] table"):
            loads('lock-version = "1.0"\n')

    def test_package_missing_name_is_lockerror_not_keyerror(self):
        body = VALID.replace('name = "kivy"\n', "")
        with pytest.raises(LockError, match="malformed"):
            loads(body)

    def test_wheel_missing_name_is_lockerror(self):
        body = VALID.replace(
            'name = "kivy-3.0.0-cp315-cp315-ios_13_0_arm64_iphoneos.whl"\n', ""
        )
        with pytest.raises(LockError):
            loads(body)

    def test_packages_not_a_list(self):
        body = VALID.replace("[[packages]]", "packages = 'nope'", 1)
        # The replacement leaves stray keys, but the scalar `packages` trips the
        # array check (or TOML parse) first; either way it's a clean LockError.
        with pytest.raises(LockError):
            loads(body)


class TestFutureSchema:
    def test_future_lock_version_rejected(self):
        body = VALID.replace('lock-version = "1.0"', 'lock-version = "2.0"')
        with pytest.raises(LockError, match="lock-version 2.0 is newer"):
            loads(body)

    def test_noninteger_lock_version_rejected(self):
        body = VALID.replace('lock-version = "1.0"', 'lock-version = "abc"')
        with pytest.raises(LockError, match="not a valid version"):
            loads(body)

    def test_future_tool_schema_version_rejected(self):
        body = VALID.replace("schema_version = 1", "schema_version = 99")
        with pytest.raises(LockError, match="schema_version 99 is newer"):
            loads(body)


class TestRequiredFields:
    def test_missing_python_xcframework_rejected(self):
        body = VALID.split("[tool.kivy_ios.python_xcframework]")[0]
        with pytest.raises(LockError, match="python_xcframework"):
            loads(body)

    def test_empty_python_xcframework_field_rejected(self):
        body = VALID.replace('version = "3.15.0"', 'version = ""')
        with pytest.raises(LockError, match="version is missing or empty"):
            loads(body)
