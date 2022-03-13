# Changelog

## [1.3.0] - 2022-03-13

### Added
- Add native support for Apple Silicon [\#660](https://github.com/kivy/kivy-ios/pull/660) ([misl6](https://github.com/misl6))
- Makes \_bz2 module available [\#658](https://github.com/kivy/kivy-ios/pull/658) ([misl6](https://github.com/misl6))
- enable sdl2 image provider to allow image to be saved from widget [\#656](https://github.com/kivy/kivy-ios/pull/656) ([brentpicasso](https://github.com/brentpicasso))
- Add MANIFEST.in [\#651](https://github.com/kivy/kivy-ios/pull/651) ([misl6](https://github.com/misl6))
- Add official OSI name in the license metadata [\#639](https://github.com/kivy/kivy-ios/pull/639) ([ecederstrand](https://github.com/ecederstrand))
- Enables buildozer to automatically install dependencies [\#638](https://github.com/kivy/kivy-ios/pull/638) ([meow464](https://github.com/meow464))
- Add bitcode support [\#605](https://github.com/kivy/kivy-ios/pull/605) ([kewlbear](https://github.com/kewlbear))
- Add the ability to clean a custom recipe, use the custom recipe instead of the bundled one, if available. [\#602](https://github.com/kivy/kivy-ios/pull/602) ([misl6](https://github.com/misl6))
- Add an error to FAQ [\#586](https://github.com/kivy/kivy-ios/pull/586) ([mvasilkov](https://github.com/mvasilkov))

### Removed
- Remove NO\_CONFIG and NO\_FILE\_LOG [\#670](https://github.com/kivy/kivy-ios/pull/670) ([akshayaurora](https://github.com/akshayaurora))
- Remove i386 and armv7 references from docs and code. Both are unsupported since a while. [\#610](https://github.com/kivy/kivy-ios/pull/610) ([misl6](https://github.com/misl6))

### Fixed
- Bump Kivy version to 2.1.0 [\#679](https://github.com/kivy/kivy-ios/pull/679) ([misl6](https://github.com/misl6))
- CI: Use a Kivy-ios installation for tests, instead of the legacy toolchain.py [\#653](https://github.com/kivy/kivy-ios/pull/653) ([misl6](https://github.com/misl6))
- Fix outdated freetype url [\#632](https://github.com/kivy/kivy-ios/pull/632) ([misl6](https://github.com/misl6))
- Bump sdl2\_ttf to 2.0.15 to improve compatibility with kivymd [\#624](https://github.com/kivy/kivy-ios/pull/624) ([brentpicasso](https://github.com/brentpicasso))
- add leading whitespace for include file [\#623](https://github.com/kivy/kivy-ios/pull/623) ([brentpicasso](https://github.com/brentpicasso))
- fix icon generation [\#620](https://github.com/kivy/kivy-ios/pull/620) ([akshayaurora](https://github.com/akshayaurora))
- Switch to iOS 9.0 where applicable [\#611](https://github.com/kivy/kivy-ios/pull/611) ([misl6](https://github.com/misl6))
- Pillow recipe rework + upgrade to version 8.2.0 [\#606](https://github.com/kivy/kivy-ios/pull/606) ([misl6](https://github.com/misl6))
- Update numpy to version 1.20.2 [\#604](https://github.com/kivy/kivy-ios/pull/604) ([misl6](https://github.com/misl6))
- Upgrade python version to 3.9.2 [\#601](https://github.com/kivy/kivy-ios/pull/601) ([misl6](https://github.com/misl6))

## [1.2.1] - 2021-01-26
### Fixed
- Fixes hostpython3 recipe on MacOS 11.1 BigSur [\#581](https://github.com/kivy/kivy-ios/issues/581) ([misl6](https://github.com/misl6))
- Fixes iOS Simulator on latest Xcode [\#571](https://github.com/kivy/kivy-ios/issues/571) ([misl6](https://github.com/misl6))
- Fixes Pillow build on Xcode 12.2 [\#579](https://github.com/kivy/kivy-ios/issues/579) ([misl6](https://github.com/misl6))
- Cookiecutter: Fixes header and library search paths on Release [\#582](https://github.com/kivy/kivy-ios/issues/582) ([misl6](https://github.com/misl6))

## [1.2.0] - 2020-12-26
### Added
- :books: Advise on using a venv [\#495](https://github.com/kivy/kivy-ios/issues/495) ([AndreMiras](https://github.com/AndreMiras))
- Add custom recipes [\#417](https://github.com/kivy/kivy-ios/issues/417) ([misl6](https://github.com/misl6))
- Add feature request template [\#557](https://github.com/kivy/kivy-ios/issues/557) ([Zen-CODE](https://github.com/Zen-CODE))
- Add instruction for cleaning cache and the build directory [\#558](https://github.com/kivy/kivy-ios/issues/558) ([Zen-CODE](https://github.com/Zen-CODE))

### Removed
- Remove distribute recipe [\#507](https://github.com/kivy/kivy-ios/issues/507) ([Zen-CODE](https://github.com/Zen-CODE))
- Remove PY2 legacy blocks from coockiecutter main.m [\#522](https://github.com/kivy/kivy-ios/issues/522) ([Zen-CODE](https://github.com/Zen-CODE))
- Remove outdated pil and pkgresources recipes [\#524](https://github.com/kivy/kivy-ios/issues/524) ([Zen-CODE](https://github.com/Zen-CODE))
- Removed broken packages listing for non-existing packages [\#525](https://github.com/kivy/kivy-ios/issues/525) ([Zen-CODE](https://github.com/Zen-CODE))

### Fixed
- :bug: fixes flake8 errors post update [\#496](https://github.com/kivy/kivy-ios/issues/496) ([AndreMiras](https://github.com/AndreMiras))
- Updates netifaces recipe, leverages `python_depends` [\#490](https://github.com/kivy/kivy-ios/issues/490) ([AndreMiras](https://github.com/AndreMiras))
- Fix pillow recipe [\#498](https://github.com/kivy/kivy-ios/issues/498) ([Zen-CODE](https://github.com/Zen-CODE))
- Fix/pillow [\#500](https://github.com/kivy/kivy-ios/issues/500) ([Zen-CODE](https://github.com/Zen-CODE))
- Fix wekzeug recipe [\#501](https://github.com/kivy/kivy-ios/issues/501) ([Zen-CODE](https://github.com/Zen-CODE))
- Fix markupsafe recipe [\#505](https://github.com/kivy/kivy-ios/issues/505) ([Zen-CODE](https://github.com/Zen-CODE))
- Fix jinja2 recipe, remove from broken list [\#508](https://github.com/kivy/kivy-ios/issues/508) ([Zen-CODE](https://github.com/Zen-CODE))
- Fix werkzeug recipe [\#509](https://github.com/kivy/kivy-ios/issues/509) ([Zen-CODE](https://github.com/Zen-CODE))
- Pin flask version and dependencies [\#510](https://github.com/kivy/kivy-ios/issues/510) ([Zen-CODE](https://github.com/Zen-CODE))
- :bug: Updates libffi download link [\#516](https://github.com/kivy/kivy-ios/issues/516) ([AndreMiras](https://github.com/AndreMiras))
- Remove --ignore-installed [\#521](https://github.com/kivy/kivy-ios/issues/521) ([misl6](https://github.com/misl6))
- Remove compile cruft after build [\#523](https://github.com/kivy/kivy-ios/issues/523) ([Zen-CODE](https://github.com/Zen-CODE))
- Move Cython requirement into requirements.txt [\#531](https://github.com/kivy/kivy-ios/issues/531) ([Zen-CODE](https://github.com/Zen-CODE))
- Fix/host setuptools3 [\#533](https://github.com/kivy/kivy-ios/issues/533) ([Zen-CODE](https://github.com/Zen-CODE))
- Fixes CI [\#569](https://github.com/kivy/kivy-ios/issues/569) ([misl6](https://github.com/misl6))
- Fix build on Xcode 12.2 [\#568](https://github.com/kivy/kivy-ios/issues/568) ([misl6](https://github.com/misl6))
- Update openssl and ffmpeg version to fix build issues [\#562](https://github.com/kivy/kivy-ios/issues/562) ([Zen-CODE](https://github.com/Zen-CODE))
- Update kivy to a post 2.0.0 version [\#575](https://github.com/kivy/kivy-ios/issues/575) ([misl6](https://github.com/misl6))

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
