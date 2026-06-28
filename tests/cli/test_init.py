"""Phase 2 — toolchain init: update path and invariants (spec 05)."""

from __future__ import annotations

import textwrap
import tomllib

import pytest
from click.testing import CliRunner

from kivy_ios.cli import init as init_mod
from kivy_ios.cli.init import init
from kivy_ios.cli.init_writer import (
    bundle_id_segment,
    has_kivy_dep,
    normalize_package_name,
    render_kivy_tables,
    strip_kivy_tables,
)
from kivy_ios.config.model import SigningConfig


@pytest.fixture
def runner():
    return CliRunner()


class TestWriterUnits:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("My App", "my_app"),
            ("kivy-ios", "kivy_ios"),
            ("123abc", "app_123abc"),
            ("Touch.Tracer", "touch_tracer"),
            ("   ", "app"),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_package_name(raw) == expected

    @pytest.mark.parametrize(
        "slug,expected",
        [
            ("hello_world", "hello-world"),
            ("myapp", "myapp"),
            ("app_123abc", "app-123abc"),
            ("touch_tracer", "touch-tracer"),
        ],
    )
    def test_bundle_id_segment(self, slug, expected):
        assert bundle_id_segment(slug) == expected

    def test_render_kivy_tables_bundle_id_has_no_underscore(self):
        block = render_kivy_tables("hello_world")
        assert 'bundle_id = "org.example.hello-world"' in block
        assert "hello_world" not in block.split("bundle_id", 1)[1].split("\n", 1)[0]

    def test_render_kivy_tables_template(self):
        block = render_kivy_tables("myapp")
        assert "[tool.kivy.ios]" in block
        assert 'bundle_id = "org.example.myapp"' in block
        assert "auto_signing = true" in block
        # template (no signing) must invite team_id, not hardcode it
        assert "TODO: set your Apple Developer Team ID" in block
        # without has_kivy there must be no exclude block
        assert "exclude" not in block

    def test_render_kivy_tables_seeds_icons_and_splash(self):
        block = render_kivy_tables("myapp")
        assert "[tool.kivy.ios.icons]" in block
        assert "[tool.kivy.ios.splash]" in block
        # icon is required for App Store submission; surface it as a TODO
        assert '# source = "assets/icon.png"' in block
        assert "App Store" in block
        assert '# source = "assets/splash.png"' in block
        assert "# background = " in block

    def test_render_kivy_tables_seeds_commented_simulator_archs(self):
        block = render_kivy_tables("myapp")
        # commented so the default (both arches) stays in effect until edited
        assert '# simulator_archs = ["arm64"]' in block

    def test_render_kivy_tables_seeds_commented_swift_packages(self):
        block = render_kivy_tables("myapp")
        # commented so a vanilla app needs no Swift toolchain until edited
        assert "# [tool.kivy.ios.native.swift_packages]" in block
        assert "sentry-cocoa" in block
        # the stub must stay inert: no active swift_packages table parsed
        from kivy_ios.config import load_config_from_text

        cfg = load_config_from_text(
            '[project]\nname = "myapp"\nversion = "1.0.0"\n\n' + block
        )
        assert cfg.ios_required.swift_packages == ()

    @pytest.mark.parametrize("has_kivy", [False, True])
    def test_render_kivy_tables_roundtrips_through_loader(self, has_kivy):
        from kivy_ios.config import load_config_from_text

        project = (
            "[project]\n"
            'name = "myapp"\n'
            'version = "1.0.0"\n'
            'dependencies = ["kivy>=3.0"]\n\n'
        )
        block = render_kivy_tables("myapp", has_kivy=has_kivy)
        cfg = load_config_from_text(project + block)
        ios = cfg.ios_required
        # commented entries leave defaults in place
        assert ios.simulator_archs == ("arm64", "x86_64")
        assert ios.icons.source is None
        assert ios.splash.source is None

    def test_render_kivy_tables_with_kivy_exclude(self):
        block = render_kivy_tables("myapp", has_kivy=True)
        assert "exclude = [" in block
        assert '"kivy-garden"' in block
        assert '"requests"' in block
        assert '"docutils"' in block
        assert '"pygments"' in block
        # each entry is annotated with its Kivy feature
        assert "RSTDocument" in block
        assert "CodeInput" in block
        assert "UrlRequest" in block
        # block is valid TOML
        import tomllib

        data = tomllib.loads(block)
        assert "kivy-garden" in data["tool"]["kivy"]["ios"]["exclude"]
        assert "docutils" in data["tool"]["kivy"]["ios"]["exclude"]

    @pytest.mark.parametrize(
        "dep,expected",
        [
            ("kivy>=3.0", True),
            ("Kivy==3.0.0", True),
            ("kivy[base]>=3.0", True),
            ("numpy>=2", False),
            ("kivy-garden>=0.1", False),  # kivy-garden is not kivy
        ],
    )
    def test_has_kivy_dep(self, dep, expected):
        assert has_kivy_dep([dep]) is expected

    def test_render_kivy_tables_preserves_signing(self):
        signing = SigningConfig(team_id="ABCDE12345", auto_signing=False)
        block = render_kivy_tables("myapp", signing=signing)
        assert 'team_id = "ABCDE12345"' in block
        assert "auto_signing = false" in block

    def test_strip_kivy_tables_keeps_project(self):
        text = textwrap.dedent(
            """
            [project]
            name = "x"  # keep this comment
            version = "1.0"

            [tool.poetry]
            foo = 1

            [tool.kivy]
            app_dir = "src"

            [tool.kivy.ios]
            schema_version = 1
            """
        ).strip()
        out = strip_kivy_tables(text)
        assert "[project]" in out
        assert "keep this comment" in out
        assert "[tool.poetry]" in out
        assert "[tool.kivy]" not in out
        assert "[tool.kivy.ios]" not in out


class TestNoManifest:
    def test_no_pyproject_no_requirements_errors(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(init, [])
        assert result.exit_code != 0
        assert "no pyproject.toml" in result.output
        assert "packaging.python.org" in result.output

    def test_requirements_only_shows_migration_message(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            (init_mod.Path(fs) / "requirements.txt").write_text("kivy\nnumpy>=2\n")
            result = runner.invoke(init, [])
        assert result.exit_code != 0
        assert "requirements.txt found" in result.output
        assert "pyproject.toml" in result.output


class TestUpdatePath:
    PYPROJECT = textwrap.dedent(
        """
        [project]
        name = "existing-app"  # keep me
        version = "2.5.0"
        dependencies = ["kivy>=3.0"]

        [tool.black]
        line-length = 100
        """
    ).strip()

    def test_update_appends_kivy_tables(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            result = runner.invoke(init, [])
            assert result.exit_code == 0, result.output
            text = pp.read_text()
            data = tomllib.loads(text)
        # [project] untouched, comment preserved
        assert data["project"]["version"] == "2.5.0"
        assert "keep me" in text
        assert data["tool"]["black"]["line-length"] == 100
        # kivy tables added, bundle_id derived from project name (underscores
        # in the slug become hyphens — bundle IDs disallow underscores)
        assert data["tool"]["kivy"]["ios"]["bundle_id"] == "org.example.existing-app"

    def test_update_with_kivy_generates_exclude_block(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            result = runner.invoke(init, [])
            assert result.exit_code == 0, result.output
            text = pp.read_text()
        assert "exclude = [" in text
        assert '"pygments"' in text
        assert "CodeInput" in text

    def test_update_refuses_without_force(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            runner.invoke(init, [])  # first add
            result = runner.invoke(init, [])  # second without force
        assert result.exit_code != 0
        assert "--force" in result.output

    def test_force_preserves_signing(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            runner.invoke(init, [])
            # user fills in signing
            text = pp.read_text().replace(
                "auto_signing = true", 'team_id = "TEAM123456"\nauto_signing = true'
            )
            pp.write_text(text)
            result = runner.invoke(init, ["--force"])
            assert result.exit_code == 0, result.output
            data = tomllib.loads(pp.read_text())
        assert data["tool"]["kivy"]["ios"]["signing"]["team_id"] == "TEAM123456"

    def test_force_preserves_python_version(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            runner.invoke(init, [])
            text = pp.read_text().replace(
                'version = "3.15.0b2"', 'version = "3.15.0b1"'
            )
            pp.write_text(text)
            result = runner.invoke(init, ["--force"])
            assert result.exit_code == 0, result.output
            data = tomllib.loads(pp.read_text())
        assert data["tool"]["kivy"]["ios"]["python"]["version"] == "3.15.0b1"

    def test_force_preserves_icon_splash_and_simulator_archs(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            runner.invoke(init, [])
            # User fills in the commented stubs with real values.
            text = pp.read_text()
            text = text.replace(
                '# simulator_archs = ["arm64"]  '
                '# drop "x86_64" once you no longer run the simulator on Intel Macs '
                "(default pins both)",
                'simulator_archs = ["arm64"]',
            )
            text = text.replace(
                '# source = "assets/icon.png"  '
                "# TODO: 1024x1024 PNG app icon — required for App Store submission",
                'source = "assets/icon.png"',
            )
            text = text.replace(
                '# source = "assets/splash.png"  # TODO: optional launch image',
                'source = "assets/splash.png"',
            )
            text = text.replace(
                '# background = "#000000"        '
                "# TODO: optional launch-screen background color",
                'background = "#112233"',
            )
            pp.write_text(text)
            result = runner.invoke(init, ["--force"])
            assert result.exit_code == 0, result.output
            data = tomllib.loads(pp.read_text())
        ios = data["tool"]["kivy"]["ios"]
        assert ios["simulator_archs"] == ["arm64"]
        assert ios["icons"]["source"] == "assets/icon.png"
        assert ios["splash"]["source"] == "assets/splash.png"
        assert ios["splash"]["background"] == "#112233"

    def test_force_keeps_stubs_when_user_set_nothing(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text(self.PYPROJECT + "\n")
            runner.invoke(init, [])
            result = runner.invoke(init, ["--force"])
            assert result.exit_code == 0, result.output
            data = tomllib.loads(pp.read_text())
            text = pp.read_text()
        ios = data["tool"]["kivy"]["ios"]
        # Untouched stubs stay commented → defaults remain in effect.
        assert "simulator_archs" not in ios
        assert ios.get("icons", {}).get("source") is None
        assert ios.get("splash", {}).get("source") is None
        assert '# simulator_archs = ["arm64"]' in text

    def test_update_refuses_without_project(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path) as fs:
            pp = init_mod.Path(fs) / "pyproject.toml"
            pp.write_text("[tool.black]\nline-length = 100\n")
            result = runner.invoke(init, [])
        assert result.exit_code != 0
        assert "no [project] table" in result.output
