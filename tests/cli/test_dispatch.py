"""Phase 0 — CLI dispatch, help, and legacy-verb migration pointers."""

from __future__ import annotations

import click
import pytest
from click.testing import CliRunner

from kivy_ios.cli import main
from kivy_ios.cli._legacy import LEGACY_VERBS

REAL_VERBS = [
    "init",
    "lock",
    "build",
    "run",
    "open",
    "upgrade",
    "clean",
    "status",
    "doctor",
]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestTopLevel:
    def test_help_lists_every_real_verb(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        for verb in REAL_VERBS:
            assert verb in result.output, f"{verb} missing from --help"

    def test_help_hides_legacy_verbs(self, runner):
        result = runner.invoke(main, ["--help"])
        # Legacy verbs are hidden; they must not appear in the command listing.
        # (Guard against a substring of a real verb by checking line starts.)
        listed = {
            line.strip().split()[0]
            for line in result.output.splitlines()
            if line.startswith("  ")
        }
        for verb in LEGACY_VERBS:
            assert verb not in listed, f"legacy verb {verb} should be hidden"

    def test_version(self, runner):
        from kivy_ios import __version__

        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestRealVerbDispatch:
    @pytest.mark.parametrize("verb", REAL_VERBS)
    def test_verb_is_dispatchable(self, runner, verb):
        # Every real verb resolves and prints per-verb help with exit 0.
        result = runner.invoke(main, [verb, "--help"])
        assert result.exit_code == 0, result.output
        assert "Usage:" in result.output

    @pytest.mark.parametrize("verb", REAL_VERBS)
    def test_verb_resolves_to_command(self, runner, verb):
        # Each verb resolves to a real click command (not "no such command").
        cmd = main.get_command(click.Context(main), cmd_name=verb)
        assert cmd is not None


class TestLegacyVerbs:
    @pytest.mark.parametrize("verb", sorted(LEGACY_VERBS))
    def test_legacy_verb_emits_pointer(self, runner, verb):
        result = runner.invoke(main, [verb])
        assert result.exit_code != 0
        assert f"'{verb}' is not a verb in kivy-ios 3.0" in result.output
        assert "kivy.org/docs/migration" in result.output

    def test_legacy_build_recipe_form(self, runner):
        # `toolchain build python3 kivy` (2.x form) gets a targeted message.
        result = runner.invoke(main, ["build", "python3", "kivy"])
        assert result.exit_code != 0
        assert "kivy-ios 2.x form" in result.output
        assert "toolchain init && toolchain lock && toolchain build" in result.output

    def test_unknown_verb_errors(self, runner):
        result = runner.invoke(main, ["frobnicate"])
        assert result.exit_code != 0
