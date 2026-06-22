"""Phase 1 — config loader happy-path + all validation rules (spec 01)."""

from __future__ import annotations

import textwrap

import pytest

from kivy_ios.config import ConfigError, load_config, load_config_from_text
from kivy_ios.config.model import SwiftPackageDep, XcframeworkDep


def load(toml: str, **kw):
    return load_config_from_text(textwrap.dedent(toml).strip(), **kw)


class TestHappyPath:
    def test_parses_valid(self, valid_toml):
        cfg = load_config_from_text(valid_toml)
        assert cfg.project.name == "touchtracer"
        assert cfg.project.version == "1.0.0"
        assert cfg.project.dependencies == ("kivy>=3.0,<4",)
        assert cfg.kivy.app_dir == "src"
        assert cfg.kivy.entry_point == "main"
        assert cfg.kivy.orientation == ("portrait", "landscape-left")
        assert cfg.display_name == "Touchtracer"
        ios = cfg.ios_required
        assert ios.bundle_id == "org.kivy.touchtracer"
        assert ios.schema_version == 1
        assert ios.python_version == "3.15.0"
        assert ios.extra_index_urls == ("https://wheels.example.com/simple",)
        assert ios.icons.source == "assets/icon.png"
        assert ios.splash.background == "#000000"
        assert ios.signing.team_id == "ABCDE12345"

    def test_defaults(self):
        cfg = load(
            """
            [project]
            name = "app"
            version = "0.1.0"
            [tool.kivy]
            app_dir = "src"
            [tool.kivy.ios]
            schema_version = 1
            bundle_id = "org.example.app"
            """
        )
        assert cfg.kivy.entry_point == "main"
        assert cfg.kivy.orientation == ("portrait",)
        ios = cfg.ios_required
        assert ios.build == 1
        assert ios.deployment_target == "13.0"
        assert ios.extra_index_urls == ()
        assert ios.signing.auto_signing is True
        assert ios.signing.upload_symbols is True
        assert cfg.display_name == "app"  # falls back to project.name

    def test_native_xcframeworks(self):
        cfg = load(
            """
            [project]
            name = "app"
            version = "0.1.0"
            [tool.kivy]
            app_dir = "src"
            [tool.kivy.ios]
            schema_version = 1
            bundle_id = "org.example.app"
            [tool.kivy.ios.native.xcframeworks]
            Sentry = { version = "8.49.0", source = "https://example.com/Sentry.zip" }
            Local = { version = "0.3.0", source = "frameworks/Local.xcframework.zip", embed = false }
            """
        )
        ios = cfg.ios_required
        assert (
            XcframeworkDep("Sentry", "8.49.0", "https://example.com/Sentry.zip")
            in ios.xcframeworks
        )
        local = next(x for x in ios.xcframeworks if x.name == "Local")
        assert local.embed is False
        assert local.link is True


def load_swift(body: str):
    """Load a minimal valid pyproject with ``body`` appended to it.

    Header and body are dedented independently so callers can pass either
    indented blocks or flat ``"\\n"``-joined strings.
    """
    header = textwrap.dedent(
        """
        [project]
        name = "app"
        version = "0.1.0"
        [tool.kivy]
        app_dir = "src"
        [tool.kivy.ios]
        schema_version = 1
        bundle_id = "org.example.app"
        """
    )
    return load_config_from_text((header + textwrap.dedent(body)).strip())


class TestSwiftPackages:
    def test_none_by_default(self):
        cfg = load_swift("")
        assert cfg.ios_required.swift_packages == ()

    def test_remote_and_local(self):
        cfg = load_swift(
            """
            [tool.kivy.ios.native.swift_packages]
            Lottie = { url = "https://github.com/airbnb/lottie-ios.git", requirement = { from = "4.4.0" }, products = ["Lottie"] }
            MyKit = { path = "vendor/MyKit", products = ["MyKit", "MyKitUI"], embed = false }
            """
        )
        pkgs = {p.name: p for p in cfg.ios_required.swift_packages}
        lottie = pkgs["Lottie"]
        assert lottie.url == "https://github.com/airbnb/lottie-ios.git"
        assert lottie.path is None
        assert lottie.requirement == {"from": "4.4.0"}
        assert lottie.products == ("Lottie",)
        assert lottie.link is True and lottie.embed is True

        mykit = pkgs["MyKit"]
        assert mykit.path == "vendor/MyKit"
        assert mykit.url is None
        assert mykit.requirement is None
        assert mykit.products == ("MyKit", "MyKitUI")
        assert mykit.embed is False

    def test_range_requirement(self):
        cfg = load_swift(
            """
            [tool.kivy.ios.native.swift_packages]
            Foo = { url = "https://example.com/foo.git", requirement = { range = ["1.0.0", "2.0.0"] }, products = ["Foo"] }
            """
        )
        (foo,) = cfg.ios_required.swift_packages
        assert foo == SwiftPackageDep(
            name="Foo",
            products=("Foo",),
            url="https://example.com/foo.git",
            requirement={"range": ["1.0.0", "2.0.0"]},
        )

    def test_table_must_be_table(self):
        with pytest.raises(ConfigError, match="must be a table"):
            load_swift("[tool.kivy.ios.native]\nswift_packages = 'nope'\n")

    def test_entry_must_be_inline_table(self):
        with pytest.raises(ConfigError, match="inline table"):
            load_swift("[tool.kivy.ios.native.swift_packages]\nFoo = 'nope'\n")

    def test_requires_url_or_path(self):
        with pytest.raises(ConfigError, match="exactly one of 'url' or 'path'"):
            load_swift(
                '[tool.kivy.ios.native.swift_packages]\nFoo = { products = ["Foo"] }\n'
            )

    def test_rejects_both_url_and_path(self):
        with pytest.raises(ConfigError, match="exactly one of 'url' or 'path'"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", path = "vendor/Foo", '
                'requirement = { from = "1.0.0" }, products = ["Foo"] }\n'
            )

    def test_remote_requires_requirement(self):
        with pytest.raises(ConfigError, match="requirement"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", products = ["Foo"] }\n'
            )

    def test_unknown_requirement_rule(self):
        with pytest.raises(ConfigError, match="unknown requirement rule"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", '
                'requirement = { latest = "yes" }, products = ["Foo"] }\n'
            )

    def test_requirement_must_have_one_rule(self):
        with pytest.raises(ConfigError, match="exactly one"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", '
                'requirement = { from = "1.0.0", exact = "1.0.0" }, '
                'products = ["Foo"] }\n'
            )

    def test_range_must_be_two_strings(self):
        with pytest.raises(ConfigError, match="two version strings"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", '
                'requirement = { range = ["1.0.0"] }, products = ["Foo"] }\n'
            )

    def test_string_requirement_must_be_nonempty(self):
        with pytest.raises(ConfigError, match="must be a non-empty string"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", '
                'requirement = { from = "" }, products = ["Foo"] }\n'
            )

    def test_local_path_must_be_relative(self):
        with pytest.raises(ConfigError, match="must be relative"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { path = "/abs/MyKit", products = ["Foo"] }\n'
            )

    def test_local_path_must_not_escape(self):
        with pytest.raises(ConfigError, match="must not escape"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { path = "../MyKit", products = ["Foo"] }\n'
            )

    def test_products_required(self):
        with pytest.raises(ConfigError, match="products"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { url = "https://x/foo.git", '
                'requirement = { from = "1.0.0" } }\n'
            )

    def test_products_must_be_nonempty(self):
        with pytest.raises(ConfigError, match="products"):
            load_swift(
                "[tool.kivy.ios.native.swift_packages]\n"
                'Foo = { path = "vendor/Foo", products = [] }\n'
            )


class TestRule1Project:
    def test_missing_project(self):
        with pytest.raises(ConfigError, match="missing \\[project\\]"):
            load("[tool.kivy]\napp_dir='src'")

    def test_missing_name(self):
        with pytest.raises(ConfigError, match="name"):
            load("[project]\nversion='1.0'\n[tool.kivy]\napp_dir='src'")

    def test_missing_version(self):
        with pytest.raises(ConfigError, match="version"):
            load("[project]\nname='a'\n[tool.kivy]\napp_dir='src'")


class TestRule2IosRequired:
    def test_missing_ios_when_required(self):
        with pytest.raises(ConfigError, match="missing \\[tool.kivy.ios\\]"):
            load(
                """
                [project]
                name='a'
                version='1.0'
                [tool.kivy]
                app_dir='src'
                """
            )

    def test_missing_ios_allowed_when_not_required(self):
        cfg = load(
            """
            [project]
            name='a'
            version='1.0'
            [tool.kivy]
            app_dir='src'
            """,
            require_ios=False,
        )
        assert cfg.ios is None


class TestRule3SchemaVersion:
    def test_missing(self):
        with pytest.raises(ConfigError, match="schema_version"):
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "[tool.kivy.ios]\nbundle_id='org.x.a'"
            )

    def test_too_new(self):
        with pytest.raises(ConfigError, match="newer than this kivy-ios") as exc:
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "[tool.kivy.ios]\nschema_version=99\nbundle_id='org.x.a'"
            )
        assert "upgrade kivy-ios" in exc.value.format()


class TestRule4BundleId:
    def test_missing(self):
        with pytest.raises(ConfigError, match="bundle_id"):
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "[tool.kivy.ios]\nschema_version=1"
            )


class TestRule5EntryPoint:
    @pytest.mark.parametrize("ep", ["123bad", "a-b", "import", "a..b", ""])
    def test_invalid(self, ep):
        with pytest.raises(ConfigError, match="entry_point"):
            load(
                f"[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                f"entry_point='{ep}'\n[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'"
            )

    def test_dotted_ok(self):
        cfg = load(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "entry_point='pkg.start'\n[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'"
        )
        assert cfg.kivy.entry_point == "pkg.start"


class TestRule6AppDir:
    @pytest.mark.parametrize("bad", [".", "", "/abs/path", "../escape"])
    def test_invalid(self, bad):
        with pytest.raises(ConfigError):
            load(
                f"[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='{bad}'\n"
                f"[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'"
            )

    def test_missing(self):
        with pytest.raises(ConfigError, match="app_dir"):
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\nentry_point='main'\n"
                "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'"
            )

    def test_nested_ok(self):
        cfg = load(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='app/src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'"
        )
        assert cfg.kivy.app_dir == "app/src"


class TestRule7Orientation:
    def test_invalid_value(self):
        with pytest.raises(ConfigError, match="orientation"):
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "orientation=['sideways']\n[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'"
            )


class TestRule8ReservedBuildSettings:
    def test_reserved_rejected(self):
        with pytest.raises(ConfigError, match="reserved"):
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
                "[tool.kivy.ios.xcode.build_settings]\nPRODUCT_BUNDLE_IDENTIFIER='x'"
            )

    def test_free_setting_ok(self):
        cfg = load(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            "[tool.kivy.ios.xcode.build_settings]\nSWIFT_VERSION='5.0'"
        )
        assert cfg.ios_required.build_settings == {"SWIFT_VERSION": "5.0"}


class TestRule10RequiresPython:
    def test_incompatible(self):
        with pytest.raises(ConfigError, match="requires-python"):
            load(
                "[project]\nname='a'\nversion='1'\nrequires-python='>=3.16'\n"
                "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
                "bundle_id='o.x.a'\n[tool.kivy.ios.python]\nversion='3.15.0'"
            )

    def test_compatible(self):
        cfg = load(
            "[project]\nname='a'\nversion='1'\nrequires-python='>=3.13'\n"
            "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
            "bundle_id='o.x.a'\n[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        assert cfg.ios_required.python_version == "3.15.0"

    def test_prerelease_needs_explicit_floor(self):
        with pytest.raises(ConfigError, match="3.15.0b2") as exc:
            load(
                "[project]\nname='a'\nversion='1'\nrequires-python='>=3.15'\n"
                "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
                "bundle_id='o.x.a'\n[tool.kivy.ios.python]\nversion='3.15.0b2'"
            )
        assert "pre-release" in str(exc.value.hint)

    def test_prerelease_with_matching_floor(self):
        cfg = load(
            "[project]\nname='a'\nversion='1'\nrequires-python='>=3.15.0b2'\n"
            "[tool.kivy]\napp_dir='src'\n[tool.kivy.ios]\nschema_version=1\n"
            "bundle_id='o.x.a'\n[tool.kivy.ios.python]\nversion='3.15.0b2'"
        )
        assert cfg.ios_required.python_version == "3.15.0b2"


class TestInfoPlistManagedKeys:
    def test_managed_key_rejected(self):
        with pytest.raises(ConfigError, match="managed"):
            load(
                "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
                "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
                "[tool.kivy.ios.info_plist]\nCFBundleIdentifier='x'"
            )

    def test_free_key_ok(self):
        cfg = load(
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            "[tool.kivy.ios.info_plist]\nNSCameraUsageDescription='QR'"
        )
        assert cfg.ios_required.info_plist == {"NSCameraUsageDescription": "QR"}


class TestFindLinks:
    def test_sibling_directory_ok(self, tmp_path):
        app = tmp_path / "hello-kivy"
        shared = tmp_path / "wheels"
        app.mkdir()
        shared.mkdir()
        toml = (
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            'find_links = ["../wheels"]\n'
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        (app / "pyproject.toml").write_text(toml)
        cfg = load_config(app / "pyproject.toml")
        assert cfg.ios_required.find_links == ("../wheels",)

    def test_escape_beyond_parent_rejected(self, tmp_path):
        app = tmp_path / "app"
        app.mkdir()
        toml = (
            "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
            "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
            'find_links = ["../../outside"]\n'
            "[tool.kivy.ios.python]\nversion='3.15.0'"
        )
        (app / "pyproject.toml").write_text(toml)
        with pytest.raises(ConfigError, match="sibling directory"):
            load_config(app / "pyproject.toml")


class TestSimulatorArchs:
    _BASE = (
        "[project]\nname='a'\nversion='1'\n[tool.kivy]\napp_dir='src'\n"
        "[tool.kivy.ios]\nschema_version=1\nbundle_id='o.x.a'\n"
    )

    def test_default_is_both_archs(self):
        cfg = load(self._BASE)
        assert cfg.ios_required.simulator_archs == ("arm64", "x86_64")

    def test_arm64_only(self):
        cfg = load(self._BASE + "simulator_archs=['arm64']\n")
        assert cfg.ios_required.simulator_archs == ("arm64",)

    def test_explicit_both(self):
        cfg = load(self._BASE + "simulator_archs=['arm64','x86_64']\n")
        assert cfg.ios_required.simulator_archs == ("arm64", "x86_64")

    def test_dedupes_preserving_order(self):
        cfg = load(self._BASE + "simulator_archs=['x86_64','arm64','x86_64']\n")
        assert cfg.ios_required.simulator_archs == ("x86_64", "arm64")

    def test_unknown_arch_rejected(self):
        with pytest.raises(ConfigError, match="unknown simulator arch"):
            load(self._BASE + "simulator_archs=['arm64','ppc']\n")

    def test_empty_rejected(self):
        with pytest.raises(ConfigError, match="must not be empty"):
            load(self._BASE + "simulator_archs=[]\n")

    def test_non_list_rejected(self):
        with pytest.raises(ConfigError, match="must be a list of strings"):
            load(self._BASE + "simulator_archs='arm64'\n")

    def test_non_string_items_rejected(self):
        with pytest.raises(ConfigError, match="must be a list of strings"):
            load(self._BASE + "simulator_archs=[1,2]\n")


class TestSyntaxError:
    def test_bad_toml_reports_line(self):
        with pytest.raises(ConfigError, match="invalid TOML"):
            load("[project]\nname = \nversion='1'")


class TestErrorFormatting:
    def test_format_includes_key_path_and_hint(self):
        try:
            load("[tool.kivy]\napp_dir='src'")
        except ConfigError as e:
            text = e.format()
            assert "project" in text
