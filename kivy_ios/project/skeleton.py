"""Minimal valid ``project.pbxproj`` skeleton for bootstrapping (spec 06).

The ``pbxproj`` library mutates an existing project; it has no from-scratch
constructor. ``toolchain build`` therefore parses this internal skeleton once
(substituting the app name + bundle id) and drives all subsequent wiring —
phases, files, build settings — through the library's API. This is *not*
user-facing cookiecutter templating: the skeleton is an implementation detail
and every meaningful object is added/synced programmatically afterwards.
"""

from __future__ import annotations

# Stable 24-hex object IDs for the skeleton. pbxproj generates fresh IDs for
# everything added later; these only need to be internally consistent.
_SKELETON = """// !$*UTF8*$!
{
\tarchiveVersion = 1;
\tclasses = {
\t};
\tobjectVersion = 56;
\tobjects = {

\t\t1A0000000000000000000001 /* Sources */ = {
\t\t\tisa = PBXSourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t1A0000000000000000000002 /* Frameworks */ = {
\t\t\tisa = PBXFrameworksBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};
\t\t1A0000000000000000000003 /* Resources */ = {
\t\t\tisa = PBXResourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t};

\t\t1A0000000000000000000010 /* {APP_NAME}.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = "{APP_NAME}.app"; sourceTree = BUILT_PRODUCTS_DIR; };

\t\t1A0000000000000000000020 = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t1A0000000000000000000021 /* Products */,
\t\t\t);
\t\t\tsourceTree = "<group>";
\t\t};
\t\t1A0000000000000000000021 /* Products */ = {
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t1A0000000000000000000010 /* {APP_NAME}.app */,
\t\t\t);
\t\t\tname = Products;
\t\t\tsourceTree = "<group>";
\t\t};

\t\t1A0000000000000000000030 /* {APP_NAME} */ = {
\t\t\tisa = PBXNativeTarget;
\t\t\tbuildConfigurationList = 1A0000000000000000000040 /* Build configuration list for PBXNativeTarget */;
\t\t\tbuildPhases = (
\t\t\t\t1A0000000000000000000001 /* Sources */,
\t\t\t\t1A0000000000000000000003 /* Resources */,
\t\t\t\t1A0000000000000000000002 /* Frameworks */,
\t\t\t);
\t\t\tbuildRules = (
\t\t\t);
\t\t\tdependencies = (
\t\t\t);
\t\t\tname = "{APP_NAME}";
\t\t\tproductName = "{APP_NAME}";
\t\t\tproductReference = 1A0000000000000000000010 /* {APP_NAME}.app */;
\t\t\tproductType = "com.apple.product-type.application";
\t\t};

\t\t1A0000000000000000000050 /* Project object */ = {
\t\t\tisa = PBXProject;
\t\t\tattributes = {
\t\t\t\tLastUpgradeCheck = 2600;
\t\t\t\tTargetAttributes = {
\t\t\t\t};
\t\t\t};
\t\t\tbuildConfigurationList = 1A0000000000000000000060 /* Build configuration list for PBXProject */;
\t\t\tcompatibilityVersion = "Xcode 14.0";
\t\t\tdevelopmentRegion = en;
\t\t\thasScannedForEncodings = 0;
\t\t\tknownRegions = (
\t\t\t\ten,
\t\t\t\tBase,
\t\t\t);
\t\t\tmainGroup = 1A0000000000000000000020;
\t\t\tproductRefGroup = 1A0000000000000000000021 /* Products */;
\t\t\tprojectDirPath = "";
\t\t\tprojectRoot = "";
\t\t\ttargets = (
\t\t\t\t1A0000000000000000000030 /* {APP_NAME} */,
\t\t\t);
\t\t};

\t\t1A0000000000000000000041 /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = "{BUNDLE_ID}";
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t};
\t\t\tname = Debug;
\t\t};
\t\t1A0000000000000000000042 /* Release */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = "{BUNDLE_ID}";
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t};
\t\t\tname = Release;
\t\t};
\t\t1A0000000000000000000040 /* Build configuration list for PBXNativeTarget */ = {
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t1A0000000000000000000041 /* Debug */,
\t\t\t\t1A0000000000000000000042 /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t};

\t\t1A0000000000000000000061 /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t};
\t\t\tname = Debug;
\t\t};
\t\t1A0000000000000000000062 /* Release */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t};
\t\t\tname = Release;
\t\t};
\t\t1A0000000000000000000060 /* Build configuration list for PBXProject */ = {
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = (
\t\t\t\t1A0000000000000000000061 /* Debug */,
\t\t\t\t1A0000000000000000000062 /* Release */,
\t\t\t);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t};
\t};
\trootObject = 1A0000000000000000000050 /* Project object */;
}
"""


def skeleton_pbxproj(app_name: str, bundle_id: str) -> str:
    return _SKELETON.replace("{APP_NAME}", app_name).replace("{BUNDLE_ID}", bundle_id)
