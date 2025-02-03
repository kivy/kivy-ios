# Changelog

## [v2024.03.17](https://github.com/kivy/kivy-ios/tree/v2024.03.17)

[Full Changelog](https://github.com/kivy/kivy-ios/compare/v2023.08.24...v2024.03.17)

**Fixed bugs:**

- zbarlite recipe has hardcoded python version [\#677](https://github.com/kivy/kivy-ios/issues/677)

**Closed issues:**

- Materialyoucolor-python Recipe [\#895](https://github.com/kivy/kivy-ios/issues/895)
- libffi recipe build hangs during configuration [\#889](https://github.com/kivy/kivy-ios/issues/889)
- Can't Input text on IOS17.2 Simulator with Xcode 15.1 [\#888](https://github.com/kivy/kivy-ios/issues/888)
- \[Request\]: Pypi packages [\#886](https://github.com/kivy/kivy-ios/issues/886)
- Add pdf2docx recipe [\#883](https://github.com/kivy/kivy-ios/issues/883)
- \[Question\] : Pygame and pyexpat ? [\#873](https://github.com/kivy/kivy-ios/issues/873)
- Support mail address is broken [\#872](https://github.com/kivy/kivy-ios/issues/872)
- Toolchain python version mismatch [\#869](https://github.com/kivy/kivy-ios/issues/869)
- how to show ip camera footage [\#868](https://github.com/kivy/kivy-ios/issues/868)
- Working app crash on iOS 17 [\#864](https://github.com/kivy/kivy-ios/issues/864)
- Crash during background execution [\#862](https://github.com/kivy/kivy-ios/issues/862)
- Python3 build fails with `unknown argument: '-fp-model'` [\#860](https://github.com/kivy/kivy-ios/issues/860)
- issue creating recipe for kiwsolver [\#857](https://github.com/kivy/kivy-ios/issues/857)
- App runs fine from XCode, but terminates with an error if installed through TestFlight [\#850](https://github.com/kivy/kivy-ios/issues/850)
- ffmpeg related errors after adding this recipe to the project [\#849](https://github.com/kivy/kivy-ios/issues/849)
- how do you init your custom c module at app startup? [\#848](https://github.com/kivy/kivy-ios/issues/848)
- Replacement for pycrypto [\#843](https://github.com/kivy/kivy-ios/issues/843)
- Xcode build fails with ModuleNotFoundError: No module named 'encodings' [\#842](https://github.com/kivy/kivy-ios/issues/842)
- Invalid Signature when adding Python to iOS App Extension [\#826](https://github.com/kivy/kivy-ios/issues/826)
- APP crashes easily [\#824](https://github.com/kivy/kivy-ios/issues/824)
- when creating xcodeproj using kivy-ios, how to change the default bundleIdentifier [\#823](https://github.com/kivy/kivy-ios/issues/823)
- toolchain build: no matching architecture in universal wrapper [\#792](https://github.com/kivy/kivy-ios/issues/792)
- Explanation to build recipe in iOS [\#776](https://github.com/kivy/kivy-ios/issues/776)
- Support arm64 simulator on Apple Silicon hardware [\#751](https://github.com/kivy/kivy-ios/issues/751)
- PyObjC import error  [\#741](https://github.com/kivy/kivy-ios/issues/741)
- App Store Connect Operation Error Invalid Bundle Structure - The binary file '\*myapp\*.app/lib/python3.9/site-packages/google/protobuf/pyext/\_message.cpython-39-darwin.so' is not permitted. [\#702](https://github.com/kivy/kivy-ios/issues/702)
- libzbar recipe missing libiconv dependency [\#676](https://github.com/kivy/kivy-ios/issues/676)
- Lib Not Found [\#674](https://github.com/kivy/kivy-ios/issues/674)
-  toolchain build kivy Error [\#668](https://github.com/kivy/kivy-ios/issues/668)
- leverage conda to create the host\* packages  [\#655](https://github.com/kivy/kivy-ios/issues/655)
- ImportError: dynamic module does not define module export function \(PyInit\_\_imaging\) [\#644](https://github.com/kivy/kivy-ios/issues/644)
- kivy ios and boto3 [\#641](https://github.com/kivy/kivy-ios/issues/641)
- Recipe for OpenCV [\#637](https://github.com/kivy/kivy-ios/issues/637)
- Issues with using threads on an iOS device [\#609](https://github.com/kivy/kivy-ios/issues/609)
- Xcode fails to build: Undefined symbols for architecture x86\_64 [\#607](https://github.com/kivy/kivy-ios/issues/607)
- There is a memory leak in the program [\#419](https://github.com/kivy/kivy-ios/issues/419)
- Include Unit tests and CI to test build for the toolchain [\#296](https://github.com/kivy/kivy-ios/issues/296)

**Merged pull requests:**

- :construction\_worker: Fix the rebuild recipe script [\#900](https://github.com/kivy/kivy-ios/pull/900) ([AndreMiras](https://github.com/AndreMiras))
- recipes: add new `materialyoucolor` recipe [\#898](https://github.com/kivy/kivy-ios/pull/898) ([T-Dynamos](https://github.com/T-Dynamos))
- Remove bitcode support, as is now deprecated by Apple [\#894](https://github.com/kivy/kivy-ios/pull/894) ([misl6](https://github.com/misl6))
- Bump openssl version to `1.1.1w` [\#891](https://github.com/kivy/kivy-ios/pull/891) ([misl6](https://github.com/misl6))
- Bump Kivy version to 2.3.0 [\#890](https://github.com/kivy/kivy-ios/pull/890) ([misl6](https://github.com/misl6))
- Set `fetch-depth: 0` for updated recipes checkout and use `actions/checkout@v4` instead of `actions/checkout@v3` [\#884](https://github.com/kivy/kivy-ios/pull/884) ([misl6](https://github.com/misl6))
- Update sdl2 deps to reflect the same targeted in kivy/kivy [\#881](https://github.com/kivy/kivy-ios/pull/881) ([misl6](https://github.com/misl6))
- Make doc structure consistent and up-to-date [\#879](https://github.com/kivy/kivy-ios/pull/879) ([Julian-O](https://github.com/Julian-O))
- Create no-response [\#878](https://github.com/kivy/kivy-ios/pull/878) ([Julian-O](https://github.com/Julian-O))
- Support Section Updated issue \#872 resolved [\#876](https://github.com/kivy/kivy-ios/pull/876) ([seharbat00l](https://github.com/seharbat00l))
- Install kivy-ios via pip during tests, so dependencies are automatically managed [\#871](https://github.com/kivy/kivy-ios/pull/871) ([misl6](https://github.com/misl6))
- Update `python3` recipe to `3.11.6` [\#870](https://github.com/kivy/kivy-ios/pull/870) ([misl6](https://github.com/misl6))
- Do not use full path for system libraries and frameworks in `.xcodeproj` [\#867](https://github.com/kivy/kivy-ios/pull/867) ([misl6](https://github.com/misl6))
- Fix for upstream issues with compiler path [\#866](https://github.com/kivy/kivy-ios/pull/866) ([tcaduser](https://github.com/tcaduser))
- update to matplotlib 3.7.2 [\#861](https://github.com/kivy/kivy-ios/pull/861) ([tcaduser](https://github.com/tcaduser))
- update for recent iOS platform changes [\#859](https://github.com/kivy/kivy-ios/pull/859) ([tcaduser](https://github.com/tcaduser))
- matplotlib recipe [\#858](https://github.com/kivy/kivy-ios/pull/858) ([tcaduser](https://github.com/tcaduser))
- Bump `numpy` version to `1.24.4` [\#856](https://github.com/kivy/kivy-ios/pull/856) ([misl6](https://github.com/misl6))
- Support ARM64 Simulator + Introduce build platform concept + Introduce `xcframework` [\#778](https://github.com/kivy/kivy-ios/pull/778) ([misl6](https://github.com/misl6))


## [v2023.08.24](https://github.com/kivy/kivy-ios/tree/v2023.08.24)

[Full Changelog](https://github.com/kivy/kivy-ios/compare/v2023.05.21...v2023.08.24)

**Fixed bugs:**

- ld: 407 duplicate symbols for architecture arm64 [\#787](https://github.com/kivy/kivy-ios/issues/787)

**Closed issues:**

- please delete [\#846](https://github.com/kivy/kivy-ios/issues/846)
- Label and MDLabel don't work correctly on iOS [\#845](https://github.com/kivy/kivy-ios/issues/845)
- ImportError: dynamic module does not define module export function \(PyInit\_\_bcrypt\) [\#841](https://github.com/kivy/kivy-ios/issues/841)
- Build failure [\#838](https://github.com/kivy/kivy-ios/issues/838)
- Custom recipes just like p4a [\#837](https://github.com/kivy/kivy-ios/issues/837)
- pandas recipe  [\#836](https://github.com/kivy/kivy-ios/issues/836)
- Build numpy: '\['/kivy/dist/hostpython3/bin/python', '-m', 'cython', '-3', '--fast-fail', '-o', '\_philox.c', '\_philox.pyx'\]' returned non-zero exit status 1.' [\#835](https://github.com/kivy/kivy-ios/issues/835)
- ios.c not found when building ios for kivy [\#833](https://github.com/kivy/kivy-ios/issues/833)
- Imvaild symlink [\#825](https://github.com/kivy/kivy-ios/issues/825)
- dynamic module does not define module export function \(PyInit\_\_multiarray\_umath\) [\#822](https://github.com/kivy/kivy-ios/issues/822)
- Toolchain build openssl not working [\#819](https://github.com/kivy/kivy-ios/issues/819)
-  OSError: codec configuration error when reading image file [\#818](https://github.com/kivy/kivy-ios/issues/818)
- Command PhaseScriptExecution failed with a nonzero exit code [\#817](https://github.com/kivy/kivy-ios/issues/817)
- We discovered that the content didn’t load after lauched.  [\#816](https://github.com/kivy/kivy-ios/issues/816)
- Asset validation failed Invalid bundle structure. The “soccer.app/lib/python3.10/site-packages/charset\_normalizer/md.cpython-310-darwin.so” binary file is not permitted.  [\#815](https://github.com/kivy/kivy-ios/issues/815)
- Asset validation failed Invalid Bundle Structure for libnpyrandom.a and libnpymath.a [\#814](https://github.com/kivy/kivy-ios/issues/814)
- kivy-ios Not found '\_SHA256.so' [\#813](https://github.com/kivy/kivy-ios/issues/813)
- The toggling of the 'readonly' attribute \(True/False\) for the MDTextField is not functioning as expected in the xcode build [\#811](https://github.com/kivy/kivy-ios/issues/811)
- libpng recipe won't build [\#808](https://github.com/kivy/kivy-ios/issues/808)
- build error in Python3.8 [\#796](https://github.com/kivy/kivy-ios/issues/796)

**Merged pull requests:**

- Use a pinned version of `Cython` for now, as most of the recipes are incompatible with `Cython==3.x.x` [\#844](https://github.com/kivy/kivy-ios/pull/844) ([misl6](https://github.com/misl6))
- Remove Unused Dependency: `requests` [\#840](https://github.com/kivy/kivy-ios/pull/840) ([gdrosos](https://github.com/gdrosos))
- Fix download from `sourceforge` \(and possibly many others\) [\#830](https://github.com/kivy/kivy-ios/pull/830) ([misl6](https://github.com/misl6))
- Now Github Actions provides `python3` via `setup-python` also for Apple Silicon macs [\#829](https://github.com/kivy/kivy-ios/pull/829) ([misl6](https://github.com/misl6))
- Bump Kivy version to 2.2.1 [\#828](https://github.com/kivy/kivy-ios/pull/828) ([misl6](https://github.com/misl6))
- Update `libpng` recipe and build `SDL2_ttf` vendored `freetype` with png support, so can render colored emoji [\#827](https://github.com/kivy/kivy-ios/pull/827) ([misl6](https://github.com/misl6))
- SDL\_ttf: Hide internal symbols via single-object prelink [\#820](https://github.com/kivy/kivy-ios/pull/820) ([misl6](https://github.com/misl6))
- Update zbarlight recipe to 3.0, refactor [\#805](https://github.com/kivy/kivy-ios/pull/805) ([Cheaterman](https://github.com/Cheaterman))
- Refactor biglink ; add extra assertions to help debug failures [\#804](https://github.com/kivy/kivy-ios/pull/804) ([Cheaterman](https://github.com/Cheaterman))


## [v2023.05.21](https://github.com/kivy/kivy-ios/tree/v2023.05.21)

[Full Changelog](https://github.com/kivy/kivy-ios/compare/v2023.01.29...v2023.05.21)

**Closed issues:**

- Issue adding Pillow to Kivy-ios build [\#807](https://github.com/kivy/kivy-ios/issues/807)
- I have created and app using kivy. it works in python through VS code but when I run throgh Xcode it gets no module named "application name" in main.py,  line number 4 error and close the app in simulator. I tried all the ways in previus discussions but still not working. is there any other way I can try?  [\#800](https://github.com/kivy/kivy-ios/issues/800)
- Kivy ios save an screen as an image to the users ios photos [\#799](https://github.com/kivy/kivy-ios/issues/799)
- Command PhaseScriptExecution failed with a nonzero exit code [\#793](https://github.com/kivy/kivy-ios/issues/793)
- ImportError: PyInit\_interval [\#788](https://github.com/kivy/kivy-ios/issues/788)
- Recipe for the cryptography module [\#786](https://github.com/kivy/kivy-ios/issues/786)
- Pyaudio [\#785](https://github.com/kivy/kivy-ios/issues/785)
- Check \#783 [\#784](https://github.com/kivy/kivy-ios/issues/784)
- Command PhaseScriptExecution failed with a nonzero exit code [\#783](https://github.com/kivy/kivy-ios/issues/783)
- Cocoapods import not found when kivy is installed [\#777](https://github.com/kivy/kivy-ios/issues/777)
- sh.CommandNotFound: /Users/suhaan/Documents/weatherappkivy/dist/hostpython3/bin/pip3 [\#775](https://github.com/kivy/kivy-ios/issues/775)
- check \#773 issue [\#774](https://github.com/kivy/kivy-ios/issues/774)
- Asset validation failed Invalid bundle structure. The “theweatherreporterapp.app/lib/python3.9/site-packages/charset\_normalizer/md\_\_mypyc.cpython-39-darwin.so” binary file is not permitted. Your app cannot contain standalone executables or libraries, other than a valid CFBundleExecutable of supported bundles. For details, visit: https://developer.apple.com/documentation/bundleresources/placing\_content\_in\_a\_bundle \(ID: eb2a7a62-515c-459b-a222-5330e609551d\) [\#773](https://github.com/kivy/kivy-ios/issues/773)
- dynamic module does not define module export function \(PyInit\_md\) error [\#772](https://github.com/kivy/kivy-ios/issues/772)
- Toolchain 407 duplicate error of arm64 [\#771](https://github.com/kivy/kivy-ios/issues/771)
- bash: toolchain: command not found [\#770](https://github.com/kivy/kivy-ios/issues/770)
- when running toolchain build python3 kivy pillow with arch arm64 with apple sicion geting list index out of range [\#769](https://github.com/kivy/kivy-ios/issues/769)
- Error compiling SDL\_Image [\#763](https://github.com/kivy/kivy-ios/issues/763)
- ImportError: dynamic module does not define module export function \(PyInit\_PIL\_\_imaging\) [\#711](https://github.com/kivy/kivy-ios/issues/711)
- Build python3 with mmap module [\#659](https://github.com/kivy/kivy-ios/issues/659)

**Merged pull requests:**

- Fix AnyIO \(and asks\) support [\#803](https://github.com/kivy/kivy-ios/pull/803) ([Cheaterman](https://github.com/Cheaterman))
- Update Kivy recipe for 2.2.0 [\#802](https://github.com/kivy/kivy-ios/pull/802) ([misl6](https://github.com/misl6))
- Use `--no-deps` and `--platform` during install of recipe python deps [\#801](https://github.com/kivy/kivy-ios/pull/801) ([misl6](https://github.com/misl6))
- Fixes crash on ios.get\_safe\_area\(\) in iOS 16 [\#790](https://github.com/kivy/kivy-ios/pull/790) ([tito](https://github.com/tito))
- Update bridge.m/h to make plyer works with severals implementation [\#789](https://github.com/kivy/kivy-ios/pull/789) ([tito](https://github.com/tito))
- Bump `numpy` version to `1.24.2` \( and fix the build on Python 3.10 ✅ \) [\#780](https://github.com/kivy/kivy-ios/pull/780) ([misl6](https://github.com/misl6))
- Disable SDL2 hidapi in order to avoid dependency on `CoreBluetooth` [\#779](https://github.com/kivy/kivy-ios/pull/779) ([misl6](https://github.com/misl6))
- 🎉 Python 3.10 support [\#768](https://github.com/kivy/kivy-ios/pull/768) ([misl6](https://github.com/misl6))
- Upgrade more GitHub Actions plus Python 3.11.1 and Cython 0.29.33 [\#767](https://github.com/kivy/kivy-ios/pull/767) ([cclauss](https://github.com/cclauss))
- Upgrade GitHub Actions [\#765](https://github.com/kivy/kivy-ios/pull/765) ([cclauss](https://github.com/cclauss))
- Update required Xcode version to 13 [\#764](https://github.com/kivy/kivy-ios/pull/764) ([misl6](https://github.com/misl6))
- Update ffmpeg/ffpyplayer versions [\#716](https://github.com/kivy/kivy-ios/pull/716) ([tito](https://github.com/tito))


## [v2023.01.29](https://github.com/kivy/kivy-ios/tree/v2023.01.29)

[Full Changelog](https://github.com/kivy/kivy-ios/compare/v2022.07.19...v2023.01.29)

**Closed issues:**

- Unknown class `<BoxShadow>` [\#758](https://github.com/kivy/kivy-ios/issues/758)
- toolchain pip3 install pycryptodome error [\#755](https://github.com/kivy/kivy-ios/issues/755)
- Stuck between two error codes: ImportError...\(PyInit\_\_imaging\) and 407 duplicate symbols [\#752](https://github.com/kivy/kivy-ios/issues/752)
- Toolchain Build error - commandnotfound python [\#748](https://github.com/kivy/kivy-ios/issues/748)
- No module named 'xxx' [\#744](https://github.com/kivy/kivy-ios/issues/744)
- dynamic module does not define module export function \(PyInit\_\_sqlite3\) [\#743](https://github.com/kivy/kivy-ios/issues/743)
- \[BUG\] Kivy Ios on mac os monterey arm64 simulator [\#740](https://github.com/kivy/kivy-ios/issues/740)
- PhaseScriptExecution failed when hitting Play in Xcode [\#739](https://github.com/kivy/kivy-ios/issues/739)
- toolchain.py build python3 openssl kivy not completing after upgrading macOS Monterey 12.5  [\#738](https://github.com/kivy/kivy-ios/issues/738)
- Proposal of versioning numbering method change for the next release [\#729](https://github.com/kivy/kivy-ios/issues/729)
- xcode archive failure- missing signing identifier ... site-packages/google/...\_api\_implementation.cpython-39-darwin.so [\#697](https://github.com/kivy/kivy-ios/issues/697)

**Merged pull requests:**

- Update pbxproj pinned version in requirements.txt [\#757](https://github.com/kivy/kivy-ios/pull/757) ([misl6](https://github.com/misl6))
- Add default Launch Screen storyboard [\#756](https://github.com/kivy/kivy-ios/pull/756) ([misl6](https://github.com/misl6))
- Flake8 does not support inline comments for any of the keys [\#754](https://github.com/kivy/kivy-ios/pull/754) ([misl6](https://github.com/misl6))
- Use Python 3.10 for tests [\#750](https://github.com/kivy/kivy-ios/pull/750) ([misl6](https://github.com/misl6))
- Update SDL2, SDL2\_ttf, SDL2\_mixer, SDL2\_image to latest releases [\#749](https://github.com/kivy/kivy-ios/pull/749) ([misl6](https://github.com/misl6))
- :rotating\_light: Minor linting fixes/updates [\#747](https://github.com/kivy/kivy-ios/pull/747) ([AndreMiras](https://github.com/AndreMiras))
- Fixes some E275 - assert is a keyword [\#746](https://github.com/kivy/kivy-ios/pull/746) ([misl6](https://github.com/misl6))
- Use `sys.executable` instead of `sh.python` [\#745](https://github.com/kivy/kivy-ios/pull/745) ([misl6](https://github.com/misl6))
- Multiple fixes to README [\#737](https://github.com/kivy/kivy-ios/pull/737) ([rshah713](https://github.com/rshah713))
- Fix typo in README [\#736](https://github.com/kivy/kivy-ios/pull/736) ([rshah713](https://github.com/rshah713))
- Disable configuration of i386-Simulator for libffi [\#761](https://github.com/kivy/kivy-ios/pull/761) ([misl6](https://github.com/misl6)

## [2022.07.19] - 2022-07-19

## Added
- Added py3dns recipe [\#728](https://github.com/kivy/kivy-ios/pull/728) ([Neizvestnyj](https://github.com/Neizvestnyj))
- Ignore egg-info in git [\#718](https://github.com/kivy/kivy-ios/pull/718) ([tito](https://github.com/tito))
- Bump Kivy recipe to a commit that includes latest camera API enhancements [\#700](https://github.com/kivy/kivy-ios/pull/700) ([RobertFlatt](https://github.com/RobertFlatt))
- Add support-requests v2 [\#689](https://github.com/kivy/kivy-ios/pull/689) ([misl6](https://github.com/misl6))

## Fixed
- Updated shebangs to target python3. Bumped libffi version to 3.4.2 [\#688](https://github.com/kivy/kivy-ios/pull/688) ([misl6](https://github.com/misl6))
- Fixes libffi 3.4.2 not linking correctly (missing symbols) on iOS Simulator [\#695](https://github.com/kivy/kivy-ios/pull/695) ([misl6](https://github.com/misl6))
- Update dpi for latest iPhone models [\#707](https://github.com/kivy/kivy-ios/pull/707) ([akshayaurora](https://github.com/akshayaurora))
- Our self-hosted Apple Silicon runner now has been migrated to actions/runner v2.292.0 which now supports arm64 natively [\#710](https://github.com/kivy/kivy-ios/pull/710) ([misl6](https://github.com/misl6))
- Update xcassets to include mandatory icons in latest xcode [\#717](https://github.com/kivy/kivy-ios/pull/717) ([tito](https://github.com/tito))
- Bump cookiecutter from 1.7.2 to 2.1.1 [\#714](https://github.com/kivy/kivy-ios/pull/714) ([dependabot](https://github.com/dependabot))
- Use shutil.which instead of sh.which [\#735](https://github.com/kivy/kivy-ios/pull/735) ([misl6](https://github.com/misl6))

## [2022.07.19] - 2022-07-19

## Added
- Added py3dns recipe [\#728](https://github.com/kivy/kivy-ios/pull/728) ([Neizvestnyj](https://github.com/Neizvestnyj))
- Ignore egg-info in git [\#718](https://github.com/kivy/kivy-ios/pull/718) ([tito](https://github.com/tito))
- Bump Kivy recipe to a commit that includes latest camera API enhancements [\#700](https://github.com/kivy/kivy-ios/pull/700) ([RobertFlatt](https://github.com/RobertFlatt))
- Add support-requests v2 [\#689](https://github.com/kivy/kivy-ios/pull/689) ([misl6](https://github.com/misl6))

## Fixed
- Updated shebangs to target python3. Bumped libffi version to 3.4.2 [\#688](https://github.com/kivy/kivy-ios/pull/688) ([misl6](https://github.com/misl6))
- Fixes libffi 3.4.2 not linking correctly (missing symbols) on iOS Simulator [\#695](https://github.com/kivy/kivy-ios/pull/695) ([misl6](https://github.com/misl6))
- Update dpi for latest iPhone models [\#707](https://github.com/kivy/kivy-ios/pull/707) ([akshayaurora](https://github.com/akshayaurora))
- Our self-hosted Apple Silicon runner now has been migrated to actions/runner v2.292.0 which now supports arm64 natively [\#710](https://github.com/kivy/kivy-ios/pull/710) ([misl6](https://github.com/misl6))
- Update xcassets to include mandatory icons in latest xcode [\#717](https://github.com/kivy/kivy-ios/pull/717) ([tito](https://github.com/tito))
- Bump cookiecutter from 1.7.2 to 2.1.1 [\#714](https://github.com/kivy/kivy-ios/pull/714) ([dependabot](https://github.com/dependabot))
- Use shutil.which instead of sh.which [\#735](https://github.com/kivy/kivy-ios/pull/735) ([misl6](https://github.com/misl6))

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
