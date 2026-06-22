# Kivy for iOS


[![Backers on Open Collective](https://opencollective.com/kivy/backers/badge.svg)](https://opencollective.com/kivy)
[![Sponsors on Open Collective](https://opencollective.com/kivy/sponsors/badge.svg)](https://opencollective.com/kivy)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)

![PyPI - Version](https://img.shields.io/pypi/v/kivy-ios)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kivy-ios)

[![kivy-ios](https://github.com/kivy/kivy-ios/actions/workflows/kivy_ios.yml/badge.svg)](https://github.com/kivy/kivy-ios/actions/workflows/kivy_ios.yml)

Kivy for iOS (kivy-ios) is a declarative toolchain that bundles
[Kivy](https://kivy.org) (and other Python) applications into an
[Xcode](https://developer.apple.com/xcode/) project ready to run on
[iOS](https://www.apple.com/ios/). You describe your app in `pyproject.toml`;
the toolchain resolves your dependencies into a lockfile, downloads the official
[`Python.xcframework`](https://www.python.org/downloads/) plus prebuilt iOS
wheels, and generates the `.xcodeproj` for you.

> **kivy-ios 3.0 (in development).** This branch replaces the legacy
> recipe/compilation system with a declarative, wheel-based workflow. If you need
> the recipe-based toolchain, use a 2.x release.

The toolchain supports:

- iPhone / iPad — iOS device (arm64)
- iOS Simulator (arm64, x86_64)

Because Xcode only runs on macOS, Kivy for iOS is only useful on this platform.

Kivy for iOS is managed by the [Kivy Team](https://kivy.org/about.html).

## Requirements

- macOS with [Xcode](https://developer.apple.com/xcode/) installed, either from
  the [Mac App Store](https://apps.apple.com/app/xcode/id497799835) or from the
  command line:

      xcode-select --install

- Accept the Xcode license once:

      sudo xcodebuild -license

## Installation

Use a Python virtual environment (host Python 3.13+). This is required: it
isolates the toolchain and keeps its lockfile resolution from being polluted by
packages in your system Python.

      python3 -m venv .venv
      . .venv/bin/activate

Install kivy-ios 3.0 from this repository (3.0 is not yet published to PyPI):

      pip install -e ".[dev]"

> **Detailed documentation.** For the full design and reference docs — the
> `pyproject.toml` / `pylock.ios.toml` schemas, artifact distribution, the CLI
> shape, and Xcode project generation — see the
> [kivy-ios 3.0 docs](docs/proposals/00-overview.md).

## Quick start

Run every command from the directory that contains your app's `pyproject.toml`.

      # 1. Seed [tool.kivy] / [tool.kivy.ios] config into pyproject.toml
      toolchain init

      # 2. Resolve dependencies into pylock.ios.toml
      toolchain lock

      # 3. Download artifacts and generate <app>-ios/<app>.xcodeproj
      toolchain build

      # 4a. Open the project in Xcode and press Run...
      toolchain open

      # 4b. ...or build, install, and launch on the simulator from the CLI
      toolchain build --simulator
      toolchain run --simulator

See the runnable examples for complete, copy-pasteable walk-throughs:

- [`examples/hello-world`](examples/hello-world/) — pure-Python smoke test using
  the official python.org `Python.xcframework` (no Kivy, no wheels).
- [`examples/hello-kivy`](examples/hello-kivy/) — minimal Kivy UI that uses
  locally built `cp315` iOS wheels from the shared [`examples/wheels/`](examples/wheels/) directory.
- [`examples/svg-explorer`](examples/svg-explorer/) — interactive SVG viewer
  (multitouch pan/zoom/rotate) using the same shared wheels.
- [`examples/pyobjus-ball`](examples/pyobjus-ball/) — calls native iOS APIs
  (CoreMotion, UIScreen) from Python via the Objective-C runtime.
- [`examples/keychain-spm`](examples/keychain-spm/) — declares a remote Swift
  Package (`KeychainAccess`), pins it with `toolchain lock`, and calls it from
  Python through a local `@objc` shim package.

## Configuring your app

Your app is described declaratively in `pyproject.toml`. Standard
[PEP 621](https://peps.python.org/pep-0621/) `[project]` metadata supplies the
name, version, and runtime `dependencies`; iOS-specific settings live under
`[tool.kivy]` and `[tool.kivy.ios]`:

```toml
[project]
name = "hello-world"
version = "0.1.0"
requires-python = ">=3.15.0b2"
dependencies = []                       # PyPI/local deps resolved into the lockfile

[tool.kivy]
display_name = "Hello World"            # name shown under the icon
app_dir = "src"                         # folder containing your Python source
entry_point = "main"                    # module imported at launch (main.py)
orientation = ["portrait"]

[tool.kivy.ios]
bundle_id = "org.example.hello-world"   # reverse-DNS; UTI characters only (no underscores)
build = 1
deployment_target = "13.0"
# find_links = ["../wheels"]            # repo-relative wheel directory for lock
# exclude = ["docutils", "pygments"]    # drop transitive deps you don't use at runtime

[tool.kivy.ios.python]
version = "3.15.0b2"                     # python.org Python.xcframework version

[tool.kivy.ios.signing]
team_id = ""                            # Apple Developer Team ID (device / release builds)
identity = "Apple Development"
auto_signing = true
```

`toolchain build` syncs your `app_dir` into the generated `<app>-ios/` tree on
every run, so make changes in your source folder (e.g. `src/`), never in the
generated project.

Kivy's wheel declares dependencies that are not all needed at runtime on iOS.
The `exclude` list trims them; the
[hello-kivy example](examples/hello-kivy/pyproject.toml) documents what each one
is for, so you can re-enable only the few that map to widgets you actually use
(e.g. `docutils` for `RSTDocument`, `pygments` for `CodeInput`, or `requests`
for `UrlRequest`).

## Commands

      toolchain init       Seed [tool.kivy] / [tool.kivy.ios] into pyproject.toml
      toolchain lock       Generate pylock.ios.toml from pyproject.toml
      toolchain build      Download artifacts, generate the Xcode project, build
      toolchain run        Build (unless --no-build), install, and launch the app
      toolchain open       Open <app>-ios/<app>.xcodeproj in Xcode
      toolchain status     Show app identity, Python version, lock sync, build state
      toolchain clean      Remove generated artifacts in the project folder
      toolchain upgrade    Re-fetch pinned Python.xcframework / xcframework artifacts
      toolchain doctor     Run environment and project health checks

Run `toolchain <command> -h` for the full set of options on any verb. A few
common ones:

- `toolchain lock --check` — CI pre-flight; exits non-zero if the lock is stale.
- `toolchain build --simulator | --device | --release` — pick the build flavor.
- `toolchain run --list-devices` — list available simulators and devices.
- `toolchain clean --cache` — also flush the artifact download cache.

Downloaded artifacts (`Python.xcframework` and other xcframeworks) are cached
under `~/Library/Caches/kivy-ios/artifacts/` and shared across projects.

## Typical workflow

A normal session is a one-time setup followed by a tight edit → run loop.
The generated project **links** your source directory (`app/` is a symlink to
`app_dir`), so editing Python source needs no rebuild — just relaunch. You only
re-run `toolchain lock` when dependencies change, and `toolchain build` when you
change app config (or need to regenerate the Xcode project).

```mermaid
flowchart TD
    A["toolchain init<br/>seed pyproject.toml"] --> B["Edit pyproject.toml<br/>dependencies + app config"]
    B --> C["Write your app<br/>src/main.py"]
    C --> D["toolchain lock<br/>→ pylock.ios.toml"]
    D --> E["toolchain build<br/>fetch artifacts + generate .xcodeproj"]
    E --> F{"Launch it"}
    F -->|from the CLI| G["toolchain run --simulator"]
    F -->|from Xcode| H["toolchain open → ⌘R"]
    G --> I(["Iterate"])
    H --> I
    I -->|changed Python source| F
    I -->|changed app config| E
    I -->|changed dependencies| D
```

Supporting commands fit around this loop: `toolchain status` shows whether your
lock and build are current, `toolchain doctor` diagnoses environment problems,
`toolchain upgrade` re-fetches the pinned runtime, and `toolchain clean` resets
the generated project when you want a fresh build.

## Development

Clone the repository and install it into a virtual environment:

      git clone https://github.com/kivy/kivy-ios.git
      cd kivy-ios/
      python3 -m venv .venv
      . .venv/bin/activate
      pip install -e ".[dev]"

Run the test suite and the linter:

      pytest
      ruff check .

## FAQ

For troubleshooting advice and other frequently asked questions, consult
the latest 
[Kivy for iOS FAQ](https://github.com/kivy/kivy-ios/blob/master/FAQ.md).

## License

Kivy for iOS is [MIT licensed](LICENSE), actively developed by a great
community and is supported by many projects managed by the 
[Kivy Organization](https://www.kivy.org/about.html).

## Support

Are you having trouble using kivy-ios or any of its related projects in the Kivy
ecosystem?
Is there an error you don’t understand? Are you trying to figure out how to use 
it? We have volunteers who can help!

The best channels to contact us for support are listed in the latest 
[Contact Us](https://github.com/kivy/kivy-ios/blob/master/CONTACT.md) document.

## Contributing

kivy-ios is part of the [Kivy](https://kivy.org) ecosystem - a large group of
products used by many thousands of developers for free, but it
is built entirely by the contributions of volunteers. We welcome (and rely on) 
users who want to give back to the community by contributing to the project.

Contributions can come in many forms. See the latest 
[Contribution Guidelines](https://github.com/kivy/kivy-ios/blob/master/CONTRIBUTING.md)
for how you can help us.

## Code of Conduct

In the interest of fostering an open and welcoming community, we as 
contributors and maintainers need to ensure participation in our project and 
our sister projects is a harassment-free and positive experience for everyone. 
It is vital that all interaction is conducted in a manner conveying respect, 
open-mindedness and gratitude.

Please consult the [latest Kivy Code of Conduct](https://github.com/kivy/kivy/blob/master/CODE_OF_CONDUCT.md).

## Contributors

This project exists thanks to 
[all the people who contribute](https://github.com/kivy/kivy-ios/graphs/contributors).
[[Become a contributor](CONTRIBUTING.md)].

<img src="https://contrib.nn.ci/api?repo=kivy/python-for-android&pages=5&no_bot=true&radius=22&cols=18">

## Backers

Thank you to [all of our backers](https://opencollective.com/kivy)! 
🙏 [[Become a backer](https://opencollective.com/kivy#backer)]

<img src="https://opencollective.com/kivy/backers.svg?width=890&avatarHeight=44&button=false">

## Sponsors

Special thanks to 
[all of our sponsors, past and present](https://opencollective.com/kivy).
Support this project by 
[[becoming a sponsor](https://opencollective.com/kivy#sponsor)].

Here are our top current sponsors. Please click through to see their websites,
and support them as they support us. 

<!--- See https://github.com/orgs/kivy/discussions/15 for explanation of this code. -->
<a href="https://opencollective.com/kivy/sponsor/0/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/1/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/2/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/3/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/3/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/4/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/5/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/6/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/7/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/7/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/8/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/9/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/9/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/10/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/10/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/11/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/11/avatar.svg"></a>

<a href="https://opencollective.com/kivy/sponsor/12/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/12/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/13/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/13/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/14/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/14/avatar.svg"></a>
<a href="https://opencollective.com/kivy/sponsor/15/website" target="_blank"><img src="https://opencollective.com/kivy/sponsor/15/avatar.svg"></a>
