"""Typed model of the kivy-ios ``pyproject.toml`` surface (spec 01).

These dataclasses are the validated, in-memory representation produced by
``kivy_ios.config.loader.load_config``. They intentionally only model the
fields kivy-ios consumes; unknown keys elsewhere in ``pyproject.toml`` are
ignored (PEP 518 tool-namespace convention).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The iOS schema major version this build understands (spec 01).
SUPPORTED_IOS_SCHEMA_VERSION = 1

VALID_ORIENTATIONS = frozenset(
    {"portrait", "portrait-upside-down", "landscape-left", "landscape-right"}
)

DEFAULT_DEPLOYMENT_TARGET = "13.0"
DEFAULT_ENTRY_POINT = "main"
DEFAULT_ORIENTATION = ("portrait",)

# Simulator architectures pinned by ``toolchain lock`` (spec 01/02). The device
# slice is always arm64; these are the *simulator* slices. ``x86_64`` exists only
# to run the simulator on an Intel Mac, so a project that no longer targets Intel
# hosts may set ``simulator_archs = ["arm64"]`` and stop pinning the dying slice.
VALID_SIMULATOR_ARCHS = frozenset({"arm64", "x86_64"})
DEFAULT_SIMULATOR_ARCHS = ("arm64", "x86_64")

# Info.plist keys kivy-ios writes from the schema; users may not set these via
# [tool.kivy.ios.info_plist] (spec 01).
MANAGED_INFO_PLIST_KEYS = frozenset(
    {
        "CFBundleName",
        "CFBundleDisplayName",
        "CFBundleIdentifier",
        "CFBundleShortVersionString",
        "CFBundleVersion",
        "MinimumOSVersion",
        "UISupportedInterfaceOrientations",
        "UISupportedInterfaceOrientations~ipad",
        "LSRequiresIPhoneOS",
        "CFBundlePackageType",
        "CFBundleInfoDictionaryVersion",
        "CFBundleExecutable",
        "NSHumanReadableCopyright",
        # SDL3 scene lifecycle — written automatically for all Kivy apps.
        "UIApplicationSceneManifest",
    }
)

# Xcode build settings the toolchain manages; rejected under
# [tool.kivy.ios.xcode.build_settings] (spec 01).
RESERVED_BUILD_SETTINGS = frozenset(
    {
        "INFOPLIST_FILE",
        "PRODUCT_BUNDLE_IDENTIFIER",
        "IPHONEOS_DEPLOYMENT_TARGET",
        "TARGETED_DEVICE_FAMILY",
        "DEBUG_INFORMATION_FORMAT",
        "CODE_SIGN_STYLE",
        "CODE_SIGN_IDENTITY",
        "DEVELOPMENT_TEAM",
        "PROVISIONING_PROFILE_SPECIFIER",
        "ENABLE_USER_SCRIPT_SANDBOXING",
        "ENABLE_TESTABILITY",
        "FRAMEWORK_SEARCH_PATHS",
        "HEADER_SEARCH_PATHS",
        "GCC_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER",
    }
)


@dataclass(frozen=True)
class Author:
    name: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class ProjectMeta:
    """PEP 621 ``[project]`` subset consumed by kivy-ios."""

    name: str
    version: str
    description: str | None = None
    requires_python: str | None = None
    dependencies: tuple[str, ...] = ()
    authors: tuple[Author, ...] = ()


@dataclass(frozen=True)
class IconConfig:
    source: str | None = None


@dataclass(frozen=True)
class SplashConfig:
    source: str | None = None
    background: str | None = None


@dataclass(frozen=True)
class XcframeworkDep:
    name: str
    version: str
    source: str
    link: bool = True
    embed: bool = True


@dataclass(frozen=True)
class SigningConfig:
    team_id: str = ""
    identity: str = "Apple Development"
    provisioning_profile: str = ""
    auto_signing: bool = True
    upload_symbols: bool = True


@dataclass(frozen=True)
class IosConfig:
    """``[tool.kivy.ios]`` overlay."""

    schema_version: int
    bundle_id: str
    build: int = 1
    deployment_target: str = DEFAULT_DEPLOYMENT_TARGET
    simulator_archs: tuple[str, ...] = DEFAULT_SIMULATOR_ARCHS
    extra_index_urls: tuple[str, ...] = ()
    find_links: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    python_version: str | None = None
    icons: IconConfig = field(default_factory=IconConfig)
    splash: SplashConfig = field(default_factory=SplashConfig)
    xcframeworks: tuple[XcframeworkDep, ...] = ()
    entitlements: dict[str, object] = field(default_factory=dict)
    signing: SigningConfig = field(default_factory=SigningConfig)
    privacy_manifest_source: str | None = None
    info_plist: dict[str, object] = field(default_factory=dict)
    build_settings: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KivyMeta:
    """Cross-platform ``[tool.kivy]`` table."""

    app_dir: str
    display_name: str | None = None
    entry_point: str = DEFAULT_ENTRY_POINT
    orientation: tuple[str, ...] = DEFAULT_ORIENTATION


@dataclass(frozen=True)
class Config:
    """Fully-validated kivy-ios project configuration."""

    project: ProjectMeta
    kivy: KivyMeta
    ios: IosConfig | None = None

    @property
    def display_name(self) -> str:
        if self.kivy.display_name:
            return self.kivy.display_name
        return self.project.name

    @property
    def app_slug(self) -> str:
        """The Xcode target / folder slug derived from [project].name."""
        return self.project.name

    @property
    def ios_required(self) -> IosConfig:
        """``[tool.kivy.ios]`` after ``load_config(..., require_ios=True)``.

        Pyright cannot infer that ``ios`` is set from the loader alone; iOS CLI
        verbs should use this accessor instead of ``config.ios`` directly.
        """
        if self.ios is None:
            raise RuntimeError(
                "Config.ios is None; call load_config with require_ios=True "
                "before accessing ios_required."
            )
        return self.ios
