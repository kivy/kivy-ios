# Changelog

## [1.1.2] - 2020-05-11
### Fixed
- Fixes (venv build) reference to SDL\_main.h [\#493](https://github.com/kivy/kivy-ios/issues/493) ([AndreMiras](https://github.com/AndreMiras))

## [1.1.1] - 2020-05-11
### Added
- Add python depends [\#455](https://github.com/kivy/kivy-ios/issues/455) ([misl6](https://github.com/misl6))

### Removed
- Removed Python 2 support [\#482](https://github.com/kivy/kivy-ios/issues/482) ([AndreMiras](https://github.com/AndreMiras))

### Fixed
- Adds initial\_working\_directory [\#489](https://github.com/kivy/kivy-ios/issues/489) ([misl6](https://github.com/misl6))
- Adds netifaces recipe, closes #239 [\#488](https://github.com/kivy/kivy-ios/issues/488) ([AndreMiras](https://github.com/AndreMiras))
- Uses contextlib.suppress to ignore exceptions [\#487](https://github.com/kivy/kivy-ios/issues/487) ([AndreMiras](https://github.com/AndreMiras))
- DRY via the find\_xcodeproj() helper method [\#486](https://github.com/kivy/kivy-ios/issues/486) ([AndreMiras](https://github.com/AndreMiras))
- Uses cd context manager in Python3Recipe.reduce\_python() [\#485](https://github.com/kivy/kivy-ios/issues/485) ([AndreMiras](https://github.com/AndreMiras))
- Uses Python 3 syntax [\#484](https://github.com/kivy/kivy-ios/issues/484) ([AndreMiras](https://github.com/AndreMiras))
- Also lints the tools/ folder [\#483](https://github.com/kivy/kivy-ios/issues/483) ([AndreMiras](https://github.com/AndreMiras))
- Migrates libffi build to Python 3 [\#481](https://github.com/kivy/kivy-ios/issues/481) ([AndreMiras](https://github.com/AndreMiras))
- Uses a couple of syntax shortcuts [\#479](https://github.com/kivy/kivy-ios/issues/479) ([AndreMiras](https://github.com/AndreMiras))
- Takes ToolchainCL definition outside the main [\#478](https://github.com/kivy/kivy-ios/issues/478) ([AndreMiras](https://github.com/AndreMiras))

## [1.1.0] - 2020-05-05
### Added
- Automatically publish to PyPI upon tagging [\#475](https://github.com/kivy/kivy-ios/issues/475) ([AndreMiras](https://github.com/AndreMiras))
- Dedicated setup.py test workflow [\#474](https://github.com/kivy/kivy-ios/issues/474) ([AndreMiras](https://github.com/AndreMiras))

### Fixed
- Fixes a regression introduced during the linting [\#477](https://github.com/kivy/kivy-ios/issues/477) ([AndreMiras](https://github.com/AndreMiras))
- More fixes to Numpy so that the binary is accepted by the App Store [\#473](https://github.com/kivy/kivy-ios/issues/473) ([lerela](https://github.com/lerela))
- Do not build known broken recipes [\#471](https://github.com/kivy/kivy-ios/issues/471) ([AndreMiras](https://github.com/AndreMiras))
- Fixes minor typos in the issue template [\#469](https://github.com/kivy/kivy-ios/issues/469) ([AndreMiras](https://github.com/AndreMiras))
- Activates venv before venv build [\#464](https://github.com/kivy/kivy-ios/issues/464) ([AndreMiras](https://github.com/AndreMiras))
- Fixes building in venv [\#462](https://github.com/kivy/kivy-ios/issues/462) ([AndreMiras](https://github.com/AndreMiras))
- Cleanup - Removes vendored deps [\#454](https://github.com/kivy/kivy-ios/issues/454) ([misl6](https://github.com/misl6))

### Changed
- Updates README.md with install/usage from PyPI [\#476](https://github.com/kivy/kivy-ios/issues/476) ([AndreMiras](https://github.com/AndreMiras))
- Moving to dedicated kivy\_ios/ package directory [\#472](https://github.com/kivy/kivy-ios/issues/472) ([AndreMiras](https://github.com/AndreMiras))
- Bumps Cython version [\#470](https://github.com/kivy/kivy-ios/issues/470) ([misl6](https://github.com/misl6))
- Uses new `cd` context manager more [\#465](https://github.com/kivy/kivy-ios/issues/465) ([AndreMiras](https://github.com/AndreMiras))


## [1.0.0] - 2020-05-02
- Initial release
