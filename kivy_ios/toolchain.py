#!/usr/bin/env python3
"""
Tool for compiling iOS toolchain
================================

This tool intend to replace all the previous tools/ in shell script.
"""

import argparse
import platform
import sys
from sys import stdout
from os.path import join, dirname, realpath, exists, isdir, basename
from os import listdir, unlink, makedirs, environ, chdir, getcwd, walk
import sh
import zipfile
import tarfile
import importlib
import json
import shutil
import fnmatch
import tempfile
import time
from contextlib import suppress
from datetime import datetime
from pprint import pformat
import logging
import urllib.request
from pbxproj import XcodeProject
from pbxproj.pbxextensions.ProjectFiles import FileOptions

url_opener = urllib.request.build_opener()
url_orig_headers = url_opener.addheaders
urllib.request.install_opener(url_opener)

curdir = dirname(__file__)

initial_working_directory = getcwd()

# For more detailed logging, use something like
# format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(funcName)s():%(lineno)d] %(message)s'
logging.basicConfig(format='[%(levelname)-8s] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

# Quiet the loggers we don't care about
sh_logging = logging.getLogger('sh')
sh_logging.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def shprint(command, *args, **kwargs):
    kwargs["_iter"] = True
    kwargs["_out_bufsize"] = 1
    kwargs["_err_to_out"] = True
    logger.info("Running Shell: {} {} {}".format(str(command), args, kwargs))
    cmd = command(*args, **kwargs)
    for line in cmd:
        # strip only last CR:
        line_str = "\n".join(line.encode("ascii", "replace").decode().splitlines())
        logger.debug(line_str)


def cache_execution(f):
    def _cache_execution(self, *args, **kwargs):
        state = self.ctx.state
        key = "{}.{}".format(self.name, f.__name__)
        force = kwargs.pop("force", False)
        if args:
            for arg in args:
                key += ".{}".format(arg)
        if key in state and not force:
            logger.debug("Cached result: {} {}. Ignoring".format(f.__name__.capitalize(), self.name))
            return
        logger.info("{} {}".format(f.__name__.capitalize(), self.name))
        f(self, *args, **kwargs)
        self.update_state(key, True)
    return _cache_execution


def remove_junk(d):
    """ Remove unused build artifacts. """
    exts = (".so.lib", ".so.o", ".sh")
    for root, dirnames, filenames in walk(d):
        for fn in filenames:
            if fn.endswith(exts):
                print('Found junk {}/{}, removing'.format(root, fn))
                unlink(join(root, fn))


class JsonStore:
    """Replacement of shelve using json, needed for support python 2 and 3.
    """

    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        if exists(filename):
            try:
                with open(filename, encoding='utf-8') as fd:
                    self.data = json.load(fd)
            except ValueError:
                logger.warning("Unable to read the state.db, content will be replaced.")

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.sync()

    def __delitem__(self, key):
        del self.data[key]
        self.sync()

    def __contains__(self, item):
        return item in self.data

    def get(self, item, default=None):
        return self.data.get(item, default)

    def keys(self):
        return self.data.keys()

    def remove_all(self, prefix):
        for key in tuple(self.data.keys()):
            if not key.startswith(prefix):
                continue
            del self.data[key]
        self.sync()

    def sync(self):
        with open(self.filename, 'w') as fd:
            json.dump(self.data, fd, ensure_ascii=False)


class GenericPlatform:
    sdk = "unspecified"
    arch = "unspecified"
    version_min = "unspecified"

    def __init__(self, ctx):
        self.ctx = ctx
        self._ccsh = None

    @property
    def name(self):
        return f"{self.sdk}-{self.arch}"

    def __str__(self):
        return self.name

    @property
    def sysroot(self):
        return sh.xcrun("--sdk", self.sdk, "--show-sdk-path").strip()

    @property
    def include_dirs(self):
        return [
            "{}/{}".format(
                self.ctx.include_dir,
                d.format(plat=self))
            for d in self.ctx.include_dirs]

    @property
    def lib_dirs(self):
        return [join(self.ctx.dist_dir, "lib", self.sdk)]

    def get_env(self):
        include_dirs = [
            "-I{}/{}".format(
                self.ctx.include_dir,
                d.format(plat=self))
            for d in self.ctx.include_dirs]
        include_dirs += ["-I{}".format(
            join(self.ctx.dist_dir, "include", self.name))]

        # Add Python include directories
        include_dirs += [
            "-I{}".format(
                join(
                    self.ctx.dist_dir,
                    "root",
                    "python3",
                    "include",
                    f"python{self.ctx.hostpython_ver}",
                )
            )
        ]

        env = {}
        cc = sh.xcrun("-find", "-sdk", self.sdk, "clang").strip()
        cxx = sh.xcrun("-find", "-sdk", self.sdk, "clang++").strip()

        # we put the flags in CC / CXX as sometimes the ./configure test
        # with the preprocessor (aka CC -E) without CFLAGS, which fails for
        # cross compiled projects
        flags = " ".join([
            "--sysroot", self.sysroot,
            "-arch", self.arch,
            "-pipe", "-no-cpp-precomp",
        ])
        cc += " " + flags
        cxx += " " + flags

        use_ccache = environ.get("USE_CCACHE", "1")
        ccache = None
        if use_ccache == "1":
            ccache = shutil.which('ccache')
        if ccache:
            ccache = ccache.strip()
            env["USE_CCACHE"] = "1"
            env["CCACHE"] = ccache
            env.update({k: v for k, v in environ.items() if k.startswith('CCACHE_')})
            env.setdefault('CCACHE_MAXSIZE', '10G')
            env.setdefault('CCACHE_HARDLINK', 'true')
            env.setdefault(
                'CCACHE_SLOPPINESS',
                ('file_macro,time_macros,'
                 'include_file_mtime,include_file_ctime,file_stat_matches'))

        if not self._ccsh:
            def noicctempfile():
                '''
                reported issue where C Python has issues with 'icc' in the compiler path
                https://github.com/python/cpython/issues/96398
                https://github.com/python/cpython/pull/96399
                '''
                while 'icc' in (x := tempfile.NamedTemporaryFile()).name:
                    pass
                return x

            self._ccsh = noicctempfile()
            self._cxxsh = noicctempfile()
            sh.chmod("+x", self._ccsh.name)
            sh.chmod("+x", self._cxxsh.name)
            self._ccsh.write(b'#!/bin/sh\n')
            self._cxxsh.write(b'#!/bin/sh\n')
            if ccache:
                logger.info("CC and CXX will use ccache")
                self._ccsh.write(
                    (ccache + ' ' + cc + ' "$@"\n').encode("utf8"))
                self._cxxsh.write(
                    (ccache + ' ' + cxx + ' "$@"\n').encode("utf8"))
            else:
                logger.info("CC and CXX will not use ccache")
                self._ccsh.write(
                    (cc + ' "$@"\n').encode("utf8"))
                self._cxxsh.write(
                    (cxx + ' "$@"\n').encode("utf8"))
            self._ccsh.flush()
            self._cxxsh.flush()

        env["CC"] = self._ccsh.name
        env["CXX"] = self._cxxsh.name
        env["AR"] = sh.xcrun("-find", "-sdk", self.sdk, "ar").strip()
        env["LD"] = sh.xcrun("-find", "-sdk", self.sdk, "ld").strip()
        env["OTHER_CFLAGS"] = " ".join(include_dirs)
        env["OTHER_LDFLAGS"] = " ".join([f"-L{d}" for d in self.lib_dirs])
        env["CFLAGS"] = " ".join([
            "-O3",
            self.version_min,
        ] + include_dirs)
        env["CXXFLAGS"] = env["CFLAGS"]
        env["LDFLAGS"] = " ".join([
            "-arch", self.arch,
            # "--sysroot", self.sysroot,
            *[f"-L{d}" for d in self.lib_dirs],
            "-L{}/usr/lib".format(self.sysroot),
            self.version_min
        ])
        return env


class iPhoneSimulatorPlatform(GenericPlatform):
    sdk = "iphonesimulator"
    version_min = "-miphonesimulator-version-min=9.0"


class iPhoneOSPlatform(GenericPlatform):
    sdk = "iphoneos"
    version_min = "-miphoneos-version-min=9.0"


class macOSPlatform(GenericPlatform):
    sdk = "macosx"
    version_min = "-mmacosx-version-min=10.9"


class iPhoneSimulatorARM64Platform(iPhoneSimulatorPlatform):
    arch = "arm64"
    triple = "aarch64-apple-darwin13"


class iPhoneSimulatorx86_64Platform(iPhoneSimulatorPlatform):
    arch = "x86_64"
    triple = "x86_64-apple-darwin13"


class iPhoneOSARM64Platform(iPhoneOSPlatform):
    arch = "arm64"
    triple = "aarch64-apple-darwin13"


class macOSx86_64Platform(macOSPlatform):
    arch = "x86_64"
    triple = "x86_64-apple-darwin13"


class macOSARM64Platform(macOSPlatform):
    arch = "arm64"
    triple = "aarch64-apple-darwin13"


class Graph:
    # Taken from python-for-android/depsort
    def __init__(self):
        # `graph`: dict that maps each package to a set of its dependencies.
        self.graph = {}

    def add(self, dependent, dependency):
        """Add a dependency relationship to the graph"""
        self.graph.setdefault(dependent, set())
        self.graph.setdefault(dependency, set())
        if dependent != dependency:
            self.graph[dependent].add(dependency)

    def add_optional(self, dependent, dependency):
        """Add an optional (ordering only) dependency relationship to the graph

        Only call this after all mandatory requirements are added
        """
        if dependent in self.graph and dependency in self.graph:
            self.add(dependent, dependency)

    def find_order(self):
        """Do a topological sort on a dependency graph

        :Parameters:
            :Returns:
                iterator, sorted items form first to last
        """
        graph = dict((k, set(v)) for k, v in self.graph.items())
        while graph:
            # Find all items without a parent
            leftmost = [name for name, dep in graph.items() if not dep]
            if not leftmost:
                raise ValueError('Dependency cycle detected! %s' % graph)
            # If there is more than one, sort them for predictable order
            leftmost.sort()
            for result in leftmost:
                # Yield and remove them from the graph
                yield result
                graph.pop(result)
                for bset in graph.values():
                    bset.discard(result)


class Context:
    env = environ.copy()
    root_dir = None
    cache_dir = None
    build_dir = None
    dist_dir = None
    install_dir = None
    ccache = None
    cython = None
    sdkver = None
    sdksimver = None
    so_suffix = None  # set by one of the hostpython

    def __init__(self):
        self.include_dirs = []

        ok = True

        sdks = sh.xcodebuild("-showsdks").splitlines()

        # get the latest iphoneos
        iphoneos = [x for x in sdks if "iphoneos" in x]
        if not iphoneos:
            logger.error("No iphone SDK installed")
            ok = False
        else:
            iphoneos = iphoneos[0].split()[-1].replace("iphoneos", "")
            self.sdkver = iphoneos

        # get the latest iphonesimulator version
        iphonesim = [x for x in sdks if "iphonesimulator" in x]
        if not iphonesim:
            ok = False
            logger.error("Error: No iphonesimulator SDK installed")
        else:
            iphonesim = iphonesim[0].split()[-1].replace("iphonesimulator", "")
            self.sdksimver = iphonesim

        # get the path for Developer
        self.devroot = "{}/Platforms/iPhoneOS.platform/Developer".format(
            sh.xcode_select("-print-path").strip())

        # path to the iOS SDK
        self.iossdkroot = "{}/SDKs/iPhoneOS{}.sdk".format(
            self.devroot, self.sdkver)

        # root of the toolchain
        self.root_dir = realpath(dirname(__file__))
        self.build_dir = "{}/build".format(initial_working_directory)
        self.cache_dir = "{}/.cache".format(initial_working_directory)
        self.dist_dir = "{}/dist".format(initial_working_directory)
        self.install_dir = "{}/dist/root".format(initial_working_directory)
        self.include_dir = "{}/dist/include".format(initial_working_directory)

        # Supported platforms may differ from default ones,
        # and the user may select to build only a subset of them via
        # --platforms command line argument.
        self.supported_platforms = [
            iPhoneOSARM64Platform(self),
            iPhoneSimulatorARM64Platform(self),
            iPhoneSimulatorx86_64Platform(self),
        ]

        # By default build the following platforms:
        # - iPhoneOSARM64Platform* (arm64)
        # - iPhoneOSSimulator*Platform (arm64 or x86_64), depending on the host
        self.default_platforms = [iPhoneOSARM64Platform(self)]
        if platform.machine() == "x86_64":
            # Intel Mac, build for iPhoneOSSimulatorx86_64Platform
            self.default_platforms.append(iPhoneSimulatorx86_64Platform(self))
        elif platform.machine() == "arm64":
            # Apple Silicon Mac, build for iPhoneOSSimulatorARM64Platform
            self.default_platforms.append(iPhoneSimulatorARM64Platform(self))

        # If the user didn't specify a platform, use the default ones.
        self.selected_platforms = self.default_platforms

        # path to some tools
        self.ccache = shutil.which("ccache")
        for cython_fn in ("cython-2.7", "cython"):
            cython = shutil.which(cython_fn)
            if cython:
                self.cython = cython
                break
        if not self.cython:
            ok = False
            logger.error("Missing requirement: cython is not installed")

        # check the basic tools
        for tool in ("pkg-config", "autoconf", "automake", "libtool"):
            if not shutil.which(tool):
                logger.error("Missing requirement: {} is not installed".format(
                    tool))

        if not ok:
            sys.exit(1)

        self.use_pigz = shutil.which('pigz')
        self.use_pbzip2 = shutil.which('pbzip2')

        try:
            num_cores = int(sh.sysctl('-n', 'hw.ncpu'))
        except Exception:
            num_cores = None
        self.num_cores = num_cores if num_cores else 4  # default to 4 if we can't detect

        self.custom_recipes_paths = []
        ensure_dir(self.root_dir)
        ensure_dir(self.build_dir)
        ensure_dir(self.cache_dir)
        ensure_dir(self.dist_dir)
        ensure_dir(join(self.dist_dir, "frameworks"))
        ensure_dir(self.install_dir)
        ensure_dir(self.include_dir)
        ensure_dir(join(self.include_dir, "common"))

        # remove the most obvious flags that can break the compilation
        self.env.pop("MACOSX_DEPLOYMENT_TARGET", None)
        self.env.pop("PYTHONDONTWRITEBYTECODE", None)
        self.env.pop("ARCHFLAGS", None)
        self.env.pop("CFLAGS", None)
        self.env.pop("LDFLAGS", None)

        # set the state
        self.state = JsonStore(join(self.dist_dir, "state.db"))

    @property
    def concurrent_make(self):
        return "-j{}".format(self.num_cores)

    @property
    def concurrent_xcodebuild(self):
        return "IDEBuildOperationMaxNumberOfConcurrentCompileTasks={}".format(self.num_cores)


class Recipe:
    props = {
        "is_alias": False,
        "version": None,
        "url": None,
        "supported_platforms": ["iphoneos-arm64", "iphonesimulator-x86_64", "iphonesimulator-arm64"],
        "depends": [],
        "optional_depends": [],
        "python_depends": [],
        "library": None,
        "libraries": [],
        "include_dir": None,
        "include_per_platform": False,
        "include_name": None,
        "frameworks": [],
        "sources": [],
        "pbx_frameworks": [],
        "pbx_libraries": [],
        "hostpython_prerequisites": []
    }

    def __new__(cls):
        for prop, value in cls.props.items():
            if not hasattr(cls, prop):
                setattr(cls, prop, value)
        return super().__new__(cls)

    # API available for recipes
    def download_file(self, url, filename, cwd=None):
        """
        Download an `url` to `outfn`
        """
        if not url:
            return

        def report_hook(index, blksize, size):
            if size <= 0:
                progression = '{0} bytes'.format(index * blksize)
            else:
                progression = '{0:.2f}%'.format(
                        index * blksize * 100. / float(size))
            stdout.write('- Download {}\r'.format(progression))
            stdout.flush()

        if cwd:
            filename = join(cwd, filename)
        with suppress(FileNotFoundError):
            unlink(filename)

        # Clean up temporary files just in case before downloading.
        urllib.request.urlcleanup()

        logger.info('Downloading {0}'.format(url))
        attempts = 0
        while True:
            try:
                url_opener.addheaders = [('User-agent', 'Wget/1.0')]
                urllib.request.urlretrieve(url, filename, report_hook)
            except OSError:
                attempts += 1
                if attempts >= 5:
                    logger.error('Max download attempts reached: {}'.format(attempts))
                    raise
                logger.warning('Download failed. Retrying in 1 second...')
                time.sleep(1)
                continue
            finally:
                url_opener.addheaders = url_orig_headers
            break

        return filename

    def extract_file(self, filename, cwd):
        """
        Extract the `filename` into the directory `cwd`.
        """
        if not filename:
            return
        logger.info("Extract {} into {}".format(filename, cwd))
        if filename.endswith((".tgz", ".tar.gz")):
            if self.ctx.use_pigz:
                comp = '--use-compress-program={}'.format(self.ctx.use_pigz)
            else:
                comp = '-z'
            shprint(sh.tar, "-C", cwd, "-xv", comp, "-f", filename)

        elif filename.endswith((".tbz2", ".tar.bz2")):
            if self.ctx.use_pbzip2:
                comp = '--use-compress-program={}'.format(self.ctx.use_pbzip2)
            else:
                comp = '-j'
            shprint(sh.tar, "-C", cwd, "-xv", comp, "-f", filename)

        elif filename.endswith(".zip"):
            shprint(sh.unzip, "-d", cwd, filename)

        else:
            logger.error("Cannot extract, unrecognized extension for {}".format(
                filename))
            raise Exception()

    def get_archive_rootdir(self, filename):
        if filename.endswith((".tgz", ".tar.gz", ".tbz2", ".tar.bz2")):
            try:
                archive = tarfile.open(filename)
            except tarfile.ReadError:
                logger.warning('Error extracting the archive {0}'.format(filename))
                logger.warning(
                    'This is usually caused by a corrupt download. The file'
                    ' will be removed and re-downloaded on the next run.')
                logger.warning(filename)
                return

            root = archive.next().path.split("/")
            return root[0]
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(filename) as zf:
                return dirname(zf.namelist()[0])
        else:
            logger.error("Unrecognized extension for {}."
                         " Cannot detect root directory".format(filename))
            raise Exception()

    def apply_patch(self, filename, target_dir=''):
        """
        Apply a patch from the current recipe directory into the current
        build directory.
        """
        target_dir = target_dir or self.build_dir
        logger.info("Apply patch {}".format(filename))
        filename = join(self.recipe_dir, filename)
        sh.patch("-t", "-d", target_dir, "-p1", "-i", filename)

    def copy_file(self, filename, dest):
        logger.info("Copy {} to {}".format(filename, dest))
        filename = join(self.recipe_dir, filename)
        dest = join(self.build_dir, dest)
        shutil.copy(filename, dest)

    def append_file(self, filename, dest):
        logger.info("Append {} to {}".format(filename, dest))
        filename = join(self.recipe_dir, filename)
        dest = join(self.build_dir, dest)
        with open(filename, "rb") as fd:
            data = fd.read()
        with open(dest, "ab") as fd:
            fd.write(data)

    def has_marker(self, marker):
        """
        Return True if the current build directory has the marker set
        """
        return exists(join(self.build_dir, ".{}".format(marker)))

    def set_marker(self, marker):
        """
        Set a marker info the current build directory
        """
        with open(join(self.build_dir, ".{}".format(marker)), "w") as fd:
            fd.write("ok")

    def delete_marker(self, marker):
        """
        Delete a specific marker
        """
        with suppress(FileNotFoundError):
            unlink(join(self.build_dir, ".{}".format(marker)))

    def get_include_dir(self):
        """
        Return the common include dir for this recipe
        """
        return join(self.ctx.include_dir, "common", self.name)

    def so_filename(self, name):
        """Return the filename of a library with the appropriate so suffix
        (.so for Python 2.7, .cpython-37m-darwin for Python 3.7)
        """
        return "{}{}".format(name, self.ctx.so_suffix)

    @property
    def name(self):
        modname = self.__class__.__module__
        return modname.split(".")[-1]

    @property
    def archive_fn(self):
        bfn = basename(self.url.format(version=self.version))
        fn = "{}/{}-{}".format(
            self.ctx.cache_dir,
            self.name, bfn)
        return fn

    @property
    def platforms_to_build(self):
        for selected_platform in self.ctx.selected_platforms:
            if selected_platform.name in self.supported_platforms:
                yield selected_platform

    @property
    def dist_xcframeworks(self):
        for lib in self._get_all_libraries():
            lib_name = basename(lib).split(".a")[0]
            yield join(self.ctx.dist_dir, "xcframework", f"{lib_name}.xcframework")

    def get_build_dir(self, plat):
        return join(self.ctx.build_dir, self.name, plat.name, self.archive_root)

    # Public Recipe API to be subclassed if needed

    def init_with_ctx(self, ctx):
        self.ctx = ctx
        include_dir = None
        if self.include_dir:
            include_name = self.include_name or self.name
            if self.include_per_platform:
                include_dir = join("{plat.name}", include_name)
            else:
                include_dir = join("common", include_name)
        if include_dir:
            logger.info("Include dir added: {}".format(include_dir))
            self.ctx.include_dirs.append(include_dir)

    def get_recipe_env(self, plat=None):
        """Return the env specialized for the recipe
        """
        if plat is None:
            plat = list(self.platforms_to_build)[0]
        return plat.get_env()

    def set_hostpython(self, instance, version):
        state = self.ctx.state
        hostpython = state.get("hostpython")
        if hostpython is None:
            state["hostpython"] = instance.name
            state.sync()
        elif hostpython != instance.name:
            logger.error("Wanted to use {}".format(instance.name))
            logger.error("but hostpython is already provided by {}.".format(
                hostpython))
            logger.error("You can have only one hostpython version compiled")
            sys.exit(1)
        self.ctx.hostpython_ver = version
        self.ctx.hostpython_recipe = instance

    def set_python(self, instance, version):
        state = self.ctx.state
        python = state.get("python")
        if python is None:
            state["python"] = instance.name
            state.sync()
        elif python != instance.name:
            logger.error("Wanted to use {}".format(instance.name))
            logger.error("but python is already provided by {}.".format(
                python))
            logger.error("You can have only one python version compiled")
            sys.exit(1)
        self.ctx.python_ver = version
        self.ctx.python_recipe = instance

    @property
    def archive_root(self):
        key = "{}.archive_root".format(self.name)
        value = self.ctx.state.get(key)
        if not value and self.url != "":
            value = self.get_archive_rootdir(self.archive_fn)
            if value is not None:
                self.ctx.state[key] = value
        return value

    def execute(self):
        if self.custom_dir:
            self.ctx.state.remove_all(self.name)
        self.download()
        self.extract()
        self.install_hostpython_prerequisites()
        self.build_all()

    @property
    def custom_dir(self):
        """Check if there is a variable name to specify a custom version /
        directory to use instead of the current url.
        """
        envname = "{}_DIR".format(self.name.upper())
        d = environ.get(envname)
        if not d:
            return
        if not exists(d):
            raise ValueError("Invalid path passed into {}".format(envname))
        return d

    def init_after_import(cls, ctx):
        """This can be used to dynamically set some variables
        depending of the state
        """
        pass

    @cache_execution
    def download(self):
        key = "{}.archive_root".format(self.name)
        if self.custom_dir:
            self.ctx.state[key] = basename(self.custom_dir)
        else:
            src_dir = join(self.recipe_dir, self.url)
            if exists(src_dir):
                self.ctx.state[key] = basename(src_dir)
                return
            fn = self.archive_fn
            if not exists(fn):
                self.download_file(self.url.format(version=self.version), fn)
            status = self.get_archive_rootdir(self.archive_fn)
            if status is not None:
                self.ctx.state[key] = status

    @cache_execution
    def extract(self):
        # recipe tmp directory
        for plat in self.platforms_to_build:
            logger.info("Extract {} for {}".format(self.name, plat.name))
            self.extract_platform(plat)

    def extract_platform(self, plat):
        build_dir = join(self.ctx.build_dir, self.name, plat.name)
        dest_dir = join(build_dir, self.archive_root)
        if self.custom_dir:
            shutil.rmtree(dest_dir, ignore_errors=True)
            shutil.copytree(self.custom_dir, dest_dir)
        else:
            if exists(dest_dir):
                return
            src_dir = join(self.recipe_dir, self.url)
            if exists(src_dir):
                shutil.copytree(src_dir, dest_dir)
                return
            ensure_dir(build_dir)
            self.extract_file(self.archive_fn, build_dir)

    @cache_execution
    def install_hostpython_prerequisites(self):
        for prerequisite in self.hostpython_prerequisites:
            _hostpython_pip(["install", prerequisite])

    @cache_execution
    def build(self, plat):
        self.build_dir = self.get_build_dir(plat)
        if self.has_marker("building"):
            logger.warning("{} build for {} has been incomplete".format(
                self.name, plat.arch))
            logger.warning("Warning: deleting the build and restarting.")
            shutil.rmtree(self.build_dir, ignore_errors=True)
            self.extract_platform(plat)

        if self.has_marker("build_done"):
            logger.info("Build python for {} already done.".format(plat.arch))
            return

        self.set_marker("building")

        chdir(self.build_dir)
        logger.info("Prebuild {} for {}".format(self.name, plat.arch))
        self.prebuild_platform(plat)
        logger.info("Build {} for {}".format(self.name, plat.arch))
        self.build_platform(plat)
        logger.info("Postbuild {} for {}".format(self.name, plat.arch))
        self.postbuild_platform(plat)
        self.delete_marker("building")
        self.set_marker("build_done")

    @cache_execution
    def build_all(self):
        logger.info("Build {} for {} (filtered)".format(
            self.name,
            ", ".join([plat.name for plat in self.platforms_to_build])
        ))

        for plat in self.platforms_to_build:
            self.build(plat)

        logger.info(f"Create lipo libraries for {self.name}")
        self.lipoize_libraries()
        logger.info(f"Create xcframeworks for {self.name}")
        self.create_xcframeworks()
        logger.info("Install include files for {}".format(self.name))
        self.install_include()
        logger.info("Install frameworks for {}".format(self.name))
        self.install_frameworks()
        logger.info("Install sources for {}".format(self.name))
        self.install_sources()
        logger.info("Install python deps for {}".format(self.name))
        self.install_python_deps()
        logger.info("Install {}".format(self.name))
        self.install()

    def prebuild_platform(self, plat):
        prebuild = "prebuild_{}".format(plat.arch)
        logger.debug("Invoking {}".format(prebuild))
        if hasattr(self, prebuild):
            getattr(self, prebuild)()

    def build_platform(self, plat):
        build = "build_{}".format(plat.arch)
        logger.debug("Invoking {}".format(build))
        if hasattr(self, build):
            getattr(self, build)()

    def postbuild_platform(self, plat):
        postbuild = "postbuild_{}".format(plat.arch)
        logger.debug("Invoking {}".format(postbuild))
        if hasattr(self, postbuild):
            getattr(self, postbuild)()
        remove_junk(self.build_dir)

    def update_state(self, key, value):
        """
        Update entry in state database. This is usually done in the
        @cache_execution decorator to log an action and its time of occurrence,
        but it needs to be done manually in recipes.
        """
        key_time = "{}.at".format(key)
        self.ctx.state[key] = value
        now_str = str(datetime.utcnow())
        self.ctx.state[key_time] = now_str
        logger.debug("New State: {} at {}".format(key, now_str))

    def _get_all_libraries(self):
        all_libraries = []
        if self.library:
            all_libraries.append(self.library)
        if self.libraries:
            all_libraries.extend(self.libraries)
        return all_libraries

    @cache_execution
    def lipoize_libraries(self):

        for library_fp in self._get_all_libraries():
            library_fn = basename(library_fp)
            logger.info("Create lipo library for {}".format(library_fn))

            # We are required to create a lipo library for each platform
            # (iPhoneOS and iPhoneSimulator are 2 different platforms)
            sdks_args = {}
            for plat in self.platforms_to_build:
                if plat.sdk not in sdks_args:
                    sdks_args[plat.sdk] = []
                sdks_args[plat.sdk].extend([
                    "-arch", plat.arch,
                    join(self.get_build_dir(plat), library_fp.format(plat=plat))
                ])

            for sdk, sdk_args in sdks_args.items():
                static_fn = join(self.ctx.dist_dir, "lib", sdk, library_fn)
                ensure_dir(dirname(static_fn))
                shprint(sh.lipo, "-create", "-output", static_fn, *sdk_args)

    @cache_execution
    def create_xcframeworks(self):
        for library_fp in self._get_all_libraries():
            library_fn = basename(library_fp)
            library_name = library_fn.split(".a")[0]

            xcframework_args = []
            for plat in self.platforms_to_build:
                static_fn = join(self.ctx.dist_dir, "lib", plat.sdk, library_fn)
                xcframework_args.extend(["-library", static_fn])

            xcframework_fn = join(self.ctx.dist_dir, "xcframework", f"{library_name}.xcframework")
            ensure_dir(dirname(xcframework_fn))
            shutil.rmtree(xcframework_fn, ignore_errors=True)
            shprint(sh.xcodebuild, "-create-xcframework", *xcframework_args, "-output", xcframework_fn)

    @cache_execution
    def install_frameworks(self):
        if not self.frameworks:
            return
        build_dir = self.get_build_dir(list(self.platforms_to_build)[0])
        for framework in self.frameworks:
            logger.info("Install Framework {}".format(framework))
            src = join(build_dir, framework)
            dest = join(self.ctx.dist_dir, "frameworks", framework)
            ensure_dir(dirname(dest))
            shutil.rmtree(dest, ignore_errors=True)
            logger.debug("Copy {} to {}".format(src, dest))
            shutil.copytree(src, dest)

    @cache_execution
    def install_sources(self):
        if not self.sources:
            return
        build_dir = self.get_build_dir(list(self.platforms_to_build)[0])
        for source in self.sources:
            logger.info("Install Sources{}".format(source))
            src = join(build_dir, source)
            dest = join(self.ctx.dist_dir, "sources", self.name)
            ensure_dir(dirname(dest))
            shutil.rmtree(dest, ignore_errors=True)
            logger.debug("Copy {} to {}".format(src, dest))
            shutil.copytree(src, dest)

    @cache_execution
    def install_include(self):
        if not self.include_dir:
            return

        include_dirs = self.include_dir
        if not isinstance(include_dirs, (list, tuple)):
            include_dirs = list([include_dirs])

        for plat in self.platforms_to_build:
            plat_dir = "common"
            if self.include_per_platform:
                plat_dir = plat.name
            include_name = self.include_name or self.name
            dest_dir = join(self.ctx.include_dir, plat_dir, include_name)
            shutil.rmtree(dest_dir, ignore_errors=True)
            build_dir = self.get_build_dir(plat)

            for include_dir in include_dirs:
                dest_name = None
                if isinstance(include_dir, (list, tuple)):
                    include_dir, dest_name = include_dir
                include_dir = include_dir.format(plat=plat, ctx=self.ctx)
                src_dir = join(build_dir, include_dir)
                if dest_name is None:
                    dest_name = basename(src_dir)
                if isdir(src_dir):
                    shutil.copytree(src_dir, dest_dir)
                else:
                    dest = join(dest_dir, dest_name)
                    logger.info("Copy Include {} to {}".format(src_dir, dest))
                    ensure_dir(dirname(dest))
                    shutil.copy(src_dir, dest)

            if not self.include_per_platform:
                # We only need to copy the include files once, even if we're
                # building for multiple platforms.
                break

    @cache_execution
    def install_python_deps(self):
        for dep in self.python_depends:
            _pip(["install", "--no-deps", "--platform", "any", dep])

    @cache_execution
    def install(self):
        pass

    @classmethod
    def list_recipes(cls, **kwargs):
        skip_list = kwargs.pop("skip_list", ['__pycache__'])
        recipes_dir = join(dirname(__file__), "recipes")
        for name in sorted(listdir(recipes_dir)):
            fn = join(recipes_dir, name)
            if isdir(fn) and name not in skip_list:
                yield name

    @classmethod
    def get_recipe(cls, name, ctx):
        if not hasattr(cls, "recipes"):
            cls.recipes = {}

        if '==' in name:
            name, version = name.split('==')
        else:
            version = None

        if name in cls.recipes:
            recipe = cls.recipes[name]
        else:
            for custom_recipe_path in ctx.custom_recipes_paths:
                if custom_recipe_path.split("/")[-1] == name:
                    spec = importlib.util.spec_from_file_location(
                        name, join(custom_recipe_path, "__init__.py")
                    )
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    recipe = mod.recipe
                    recipe.recipe_dir = custom_recipe_path
                    logger.info(f"A custom version for recipe '{name}' found in folder {custom_recipe_path}")
                    break
            else:
                logger.info(f"Using the bundled version for recipe '{name}'")
                mod = importlib.import_module(f"kivy_ios.recipes.{name}")
                recipe = mod.recipe
                recipe.recipe_dir = join(ctx.root_dir, "recipes", name)

            recipe.init_after_import(ctx)

        if version:
            recipe.version = version

        return recipe


class HostRecipe(Recipe):

    @property
    def supported_platforms(self):
        if platform.machine() == 'x86_64':
            return ["macosx-x86_64"]
        elif platform.machine() == 'arm64':
            return ["macosx-arm64"]

    @property
    def platforms_to_build(self):
        for supported_platform in self.supported_platforms:
            if supported_platform == "macosx-x86_64":
                yield macOSx86_64Platform(self.ctx)
            elif supported_platform == "macosx-arm64":
                yield macOSARM64Platform(self.ctx)


class PythonRecipe(Recipe):
    @cache_execution
    def install(self):
        self.install_python_package()
        self.reduce_python_package()
        remove_junk(self.ctx.site_packages_dir)

    def install_python_package(self, name=None, env=None, is_dir=True):
        """Automate the installation of a Python package into the target
        site-packages.

        It will works with the first platforms_to_build,
        and the name of the recipe.
        """
        plat = list(self.platforms_to_build)[0]
        if name is None:
            name = self.name
        if env is None:
            env = self.get_recipe_env(plat)
        logger.info("Install {} into the site-packages".format(name))
        build_dir = self.get_build_dir(plat)
        chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)

        shprint(
            hostpython,
            "setup.py",
            "install",
            "-O2",
            "--root", self.ctx.python_prefix,
            "--prefix", "",
            _env=env,
        )

    def reduce_python_package(self):
        """Feel free to remove things you don't want in the final
        site-packages.
        """
        pass


class CythonRecipe(PythonRecipe):
    pre_build_ext = False
    cythonize = True
    hostpython_prerequisites = ["Cython==3.0.11"]

    def cythonize_file(self, filename):
        if filename.startswith(self.build_dir):
            filename = filename[len(self.build_dir) + 1:]
        logger.info("Cythonize {}".format(filename))
        # note when kivy-ios package installed the `cythonize.py` script
        # doesn't (yet) have the executable bit hence we explicitly call it
        # with the Python interpreter
        cythonize_script = join(self.ctx.root_dir, "tools", "cythonize.py")

        shprint(sh.Command(self.ctx.hostpython), cythonize_script, filename)

    def cythonize_build(self):
        if not self.cythonize:
            return
        root_dir = self.build_dir
        for root, dirnames, filenames in walk(root_dir):
            for filename in fnmatch.filter(filenames, "*.pyx"):
                self.cythonize_file(join(root, filename))

    def biglink(self):
        dirs = []
        for root, dirnames, filenames in walk(self.build_dir):
            if fnmatch.filter(filenames, "*.so.libs"):
                dirs.append(root)
        cmd = sh.Command(join(self.ctx.root_dir, "tools", "biglink"))
        shprint(cmd, join(self.build_dir, "lib{}.a".format(self.name)), *dirs)

    def get_recipe_env(self, plat):
        env = super().get_recipe_env(plat)
        env["KIVYIOSROOT"] = self.ctx.root_dir
        env["IOSSDKROOT"] = plat.sysroot
        env["CUSTOMIZED_OSX_COMPILER"] = 'True'
        env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        env["ARM_LD"] = env["LD"]
        env["PLATFORM_SDK"] = plat.sdk
        env["ARCH"] = plat.arch
        return env

    def build_platform(self, plat):
        build_env = self.get_recipe_env(plat)
        hostpython = sh.Command(self.ctx.hostpython)
        if self.pre_build_ext:
            with suppress(Exception):
                shprint(hostpython, "setup.py", "build_ext", "-g",
                        _env=build_env)
        self.cythonize_build()
        shprint(hostpython, "setup.py", "build_ext", "-g",
                _env=build_env)
        self.biglink()


def build_recipes(names, ctx):
    # gather all the dependencies
    logger.info("Want to build {}".format(names))
    graph = Graph()
    ctx.wanted_recipes = names[:]
    recipe_to_load = names
    recipe_loaded = []
    while names:
        name = recipe_to_load.pop(0)
        if name in recipe_loaded:
            continue
        try:
            recipe = Recipe.get_recipe(name, ctx)
        except KeyError:
            logger.error("No recipe named {}".format(name))
            sys.exit(1)
        graph.add(name, name)
        logger.info("Loaded recipe {} (depends of {}, optional are {})".format(
            name, recipe.depends, recipe.optional_depends))
        for depend in recipe.depends:
            graph.add(name, depend)
            recipe_to_load += recipe.depends
        for depend in recipe.optional_depends:
            # in case of compilation after the initial one, take in account
            # of the already compiled recipes
            key = "{}.build_all".format(depend)
            if key in ctx.state:
                recipe_to_load.append(name)
                graph.add(name, depend)
            else:
                graph.add_optional(name, depend)
        recipe_loaded.append(name)

    build_order = list(graph.find_order())
    logger.info("Build order is {}".format(build_order))
    recipes = [Recipe.get_recipe(name, ctx) for name in build_order]
    recipes = [recipe for recipe in recipes if not recipe.is_alias]
    recipes_order = [recipe.name for recipe in recipes]
    logger.info("Recipe order is {}".format(recipes_order))
    for recipe in recipes:
        recipe.init_with_ctx(ctx)
    for recipe in recipes:
        recipe.execute()


def ensure_dir(filename):
    makedirs(filename, exist_ok=True)


def ensure_recipes_loaded(ctx):
    for recipe in Recipe.list_recipes():
        key = "{}.build_all".format(recipe)
        if key not in ctx.state:
            continue
        recipe = Recipe.get_recipe(recipe, ctx)
        recipe.init_with_ctx(ctx)


def _pip(args):
    ctx = Context()
    for recipe in Recipe.list_recipes():
        key = "{}.build_all".format(recipe)
        if key not in ctx.state:
            continue
        recipe = Recipe.get_recipe(recipe, ctx)
        recipe.init_with_ctx(ctx)
    if not hasattr(ctx, "site_packages_dir"):
        logger.error("python must be compiled before using pip")
        sys.exit(1)

    pip_env = {
        "CC": "/bin/false",
        "CXX": "/bin/false",
        "PYTHONPATH": ctx.site_packages_dir,
        "PYTHONOPTIMIZE": "2",
        # "PIP_INSTALL_TARGET": ctx.site_packages_dir
    }

    pip_path = join(ctx.dist_dir, 'hostpython3', 'bin', 'pip3')

    if len(args) > 1 and args[0] == "install":
        pip_args = ["--isolated"]

        # --platform option requires --target, but --target can't be used
        # with --prefix. We should prefer --prefix if it's possible,
        # cause it notices already installed dependencies.
        if "--platform" in args:
            pip_args += ["--target", ctx.site_packages_dir]
        else:
            pip_args += ["--prefix", ctx.python_prefix]

        args = ["install"] + pip_args + args[1:]

    logger.info("Executing pip with: {}".format(args))
    pip_cmd = sh.Command(pip_path)
    shprint(pip_cmd, *args, _env=pip_env)


def _hostpython_pip(args):
    ctx = Context()
    pip_path = join(ctx.dist_dir, 'hostpython3', 'bin', 'pip3')
    logger.info("Executing pip for hostpython with: {}".format(args))
    pip_cmd = sh.Command(pip_path)
    shprint(pip_cmd, *args)


def update_pbxproj(filename, pbx_frameworks=None):
    # list all the compiled recipes
    ctx = Context()
    pbx_libraries = []
    if pbx_frameworks is None:
        pbx_frameworks = []
    frameworks = []
    xcframeworks = []
    sources = []
    for recipe in Recipe.list_recipes():
        key = "{}.build_all".format(recipe)
        if key not in ctx.state:
            continue
        recipe = Recipe.get_recipe(recipe, ctx)
        recipe.init_with_ctx(ctx)
        pbx_frameworks.extend(recipe.pbx_frameworks)
        pbx_libraries.extend(recipe.pbx_libraries)
        xcframeworks.extend(recipe.dist_xcframeworks)
        frameworks.extend(recipe.frameworks)
        if recipe.sources:
            sources.append(recipe.name)

    pbx_frameworks = list(set(pbx_frameworks))
    pbx_libraries = list(set(pbx_libraries))
    xcframeworks = list(set(xcframeworks))

    logger.info("-" * 70)
    logger.info("The project need to have:")
    logger.info("iOS Frameworks: {}".format(pbx_frameworks))
    logger.info("iOS Libraries: {}".format(pbx_libraries))
    logger.info("iOS local Frameworks: {}".format(frameworks))
    logger.info("XCFrameworks: {}".format(xcframeworks))
    logger.info("Sources to link: {}".format(sources))

    logger.info("-" * 70)
    logger.info("Analysis of {}".format(filename))

    project = XcodeProject.load(filename)

    group = project.get_or_create_group("Frameworks")
    g_classes = project.get_or_create_group("Classes")
    for framework in pbx_frameworks:
        framework_name = "{}.framework".format(framework)
        if framework_name in frameworks:
            logger.info("Ensure {} is in the project (pbx_frameworks, local)".format(framework))
            f_path = join(ctx.dist_dir, "frameworks", framework_name)
        else:
            logger.info("Ensure {} is in the project (pbx_frameworks, system)".format(framework))
            # We do not need to specify the full path to the framework, as
            # Xcode will search for it in the SDKs.
            f_path = framework_name
        project.add_file(
            f_path,
            parent=group,
            tree="DEVELOPER_DIR",
            force=False,
            file_options=FileOptions(
                embed_framework=False,
                code_sign_on_copy=True
            ),
        )
    for library in pbx_libraries:
        library_name = f"{library}.tbd"
        logger.info("Ensure {} is in the project (pbx_libraries, tbd)".format(library))
        # We do not need to specify the full path to the library, as
        # Xcode will search for it in the SDKs.
        project.add_file(library_name, parent=group, tree="DEVELOPER_DIR", force=False)
    for xcframework in xcframeworks:
        logger.info("Ensure {} is in the project (xcframework)".format(xcframework))
        project.add_file(
            xcframework,
            parent=group,
            force=False,
            file_options=FileOptions(embed_framework=False)
        )
    for name in sources:
        logger.info("Ensure {} sources are used".format(name))
        fn = join(ctx.dist_dir, "sources", name)
        project.add_folder(fn, parent=g_classes)

    project.backup()
    project.save()


class ToolchainCL:
    def __init__(self):
        parser = argparse.ArgumentParser(
                description="Tool for managing the iOS / Python toolchain",
                usage="""toolchain <command> [<args>]

Available commands:
build         Build a recipe (compile a library for the required target
              architecture)
clean         Clean the build of the specified recipe
distclean     Clean the build and the result
recipes       List all the available recipes
status        List all the recipes and their build status
build_info    Display the current build context and Architecture info

Xcode:
create        Create a new xcode project
update        Update an existing xcode project (frameworks, libraries..)
launchimage   Create Launch images for your xcode project
icon          Create Icons for your xcode project
pip           Install a pip dependency into the distribution
""")
        parser.add_argument("command", help="Command to run")
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    @staticmethod
    def find_xcodeproj(filename):
        if not filename.endswith(".xcodeproj"):
            # try to find the xcodeproj
            from glob import glob
            xcodeproj = glob(join(filename, "*.xcodeproj"))
            if not xcodeproj:
                logger.error("Unable to find a xcodeproj in {}".format(filename))
                sys.exit(1)
            filename = xcodeproj[0]
        return filename

    @staticmethod
    def validate_custom_recipe_paths(ctx, paths):
        for custom_recipe_path in paths:
            if exists(custom_recipe_path):
                logger.info(f"Adding {custom_recipe_path} to custom recipes paths")
                ctx.custom_recipes_paths.append(custom_recipe_path)
            else:
                logger.error(f"{custom_recipe_path} isn't a valid path")
                raise FileNotFoundError

    def build(self):
        ctx = Context()
        parser = argparse.ArgumentParser(
                description="Build the toolchain")
        parser.add_argument("recipe", nargs="+", help="Recipe to compile")
        parser.add_argument("--platform", action="append",
                            help="Restrict compilation specific platform (multiple allowed)")
        parser.add_argument("--concurrency", type=int, default=ctx.num_cores,
                            help="number of concurrent build processes (where supported)")
        parser.add_argument("--no-pigz", action="store_true", default=not bool(ctx.use_pigz),
                            help="do not use pigz for gzip decompression")
        parser.add_argument("--no-pbzip2", action="store_true", default=not bool(ctx.use_pbzip2),
                            help="do not use pbzip2 for bzip2 decompression")
        parser.add_argument("--add-custom-recipe", action="append", default=[],
                            help="Path to custom recipe")
        args = parser.parse_args(sys.argv[2:])

        if args.platform:

            # User requested a specific set of platforms, so we need to reset
            # the list of the selected platforms.
            ctx.selected_platforms = []

            for req_platform in args.platform:

                if req_platform in [plat.name for plat in ctx.selected_platforms]:
                    logger.error(f"Platform {req_platform} has been specified multiple times")
                    sys.exit(1)

                if req_platform not in [plat.name for plat in ctx.supported_platforms]:
                    logger.error(f"Platform {req_platform} is not supported")
                    sys.exit(1)

                ctx.selected_platforms.extend([plat for plat in ctx.supported_platforms if plat.name == req_platform])

            logger.info(f"The following platforms has been requested to build: {ctx.selected_platforms}")

        ctx.num_cores = args.concurrency
        if args.no_pigz:
            ctx.use_pigz = False
        if args.no_pbzip2:
            ctx.use_pbzip2 = False

        self.validate_custom_recipe_paths(ctx, args.add_custom_recipe)

        ctx.use_pigz = ctx.use_pbzip2
        logger.info("Building with {} processes, where supported".format(ctx.num_cores))
        if ctx.use_pigz:
            logger.info("Using pigz to decompress gzip data")
        if ctx.use_pbzip2:
            logger.info("Using pbzip2 to decompress bzip2 data")

        build_recipes(args.recipe, ctx)

    def recipes(self):
        parser = argparse.ArgumentParser(
                description="List all the available recipes")
        parser.add_argument(
                "--compact", action="store_true",
                help="Produce a compact list suitable for scripting")
        args = parser.parse_args(sys.argv[2:])

        if args.compact:
            print(" ".join(list(Recipe.list_recipes())))
        else:
            ctx = Context()
            for name in Recipe.list_recipes():
                with suppress(Exception):
                    recipe = Recipe.get_recipe(name, ctx)
                    print("{recipe.name:<12} {recipe.version:<8}".format(recipe=recipe))

    def clean(self):
        def clean_cache(recipe, ctx):
            """ Remove download artifacts for this build. """
            recipe_inst = Recipe.get_recipe(recipe, ctx)
            recipe_inst.ctx = ctx
            if exists(recipe_inst.archive_fn):
                unlink(recipe_inst.archive_fn)

        ctx = Context()
        parser = argparse.ArgumentParser(
                description="Clean the build")
        parser.add_argument("recipe", nargs="*", help="Recipe to clean")
        parser.add_argument("--add-custom-recipe", action="append", default=[],
                            help="Path to custom recipe")
        args = parser.parse_args(sys.argv[2:])

        self.validate_custom_recipe_paths(ctx, args.add_custom_recipe)

        if args.recipe:
            for recipe in args.recipe:
                logger.info("Cleaning {} build".format(recipe))
                ctx.state.remove_all("{}.".format(recipe))
                build_dir = join(ctx.build_dir, recipe)
                shutil.rmtree(build_dir, ignore_errors=True)
                clean_cache(recipe, ctx)
        else:
            logger.info("Delete build directory")
            shutil.rmtree(ctx.build_dir, ignore_errors=True)

    def distclean(self):
        ctx = Context()
        shutil.rmtree(ctx.build_dir, ignore_errors=True)
        shutil.rmtree(ctx.dist_dir, ignore_errors=True)
        shutil.rmtree(ctx.cache_dir, ignore_errors=True)

    def status(self):
        ctx = Context()
        for recipe in Recipe.list_recipes():
            key = "{}.build_all".format(recipe)
            keytime = "{}.build_all.at".format(recipe)

            if key in ctx.state:
                status = "Build OK (built at {})".format(ctx.state[keytime])
            else:
                status = "Not built"
            print("{:<12} - {}".format(
                recipe, status))

    def create(self):
        parser = argparse.ArgumentParser(
                description="Create a new xcode project")
        parser.add_argument("name", help="Name of your project")
        parser.add_argument("directory", help="Directory where your project lives")
        parser.add_argument("--add-framework", action="append", help="Additional Frameworks to include with this project")
        args = parser.parse_args(sys.argv[2:])

        from cookiecutter.main import cookiecutter
        ctx = Context()
        ensure_recipes_loaded(ctx)

        if not hasattr(ctx, "python_ver"):
            logger.error("No python recipe compiled!")
            logger.error("You must have compiled at least python3")
            logger.error("recipe to be able to create a project.")
            sys.exit(1)

        template_dir = join(curdir, "tools", "templates")
        context = {
            "title": args.name,
            "project_name": args.name.lower(),
            "domain_name": "org.kivy.{}".format(args.name.lower()),
            "project_dir": realpath(args.directory),
            "version": "1.0.0",
            "dist_dir": ctx.dist_dir,
        }
        cookiecutter(template_dir, no_input=True, extra_context=context)
        filename = join(
                initial_working_directory,
                "{}-ios".format(args.name.lower()),
                "{}.xcodeproj".format(args.name.lower()),
                "project.pbxproj")
        update_pbxproj(filename, pbx_frameworks=args.add_framework)
        print("--")
        print("Project directory : {}-ios".format(
            args.name.lower()))
        print("XCode project     : {0}-ios/{0}.xcodeproj".format(
            args.name.lower()))

    def update(self):
        parser = argparse.ArgumentParser(
                description="Update an existing xcode project")
        parser.add_argument("filename", help="Path to your project or xcodeproj")
        parser.add_argument("--add-framework", action="append", help="Additional Frameworks to include with this project")
        args = parser.parse_args(sys.argv[2:])

        filename = self.find_xcodeproj(args.filename)
        filename = join(filename, "project.pbxproj")
        if not exists(filename):
            logger.error("{} not found".format(filename))
            sys.exit(1)

        update_pbxproj(filename, pbx_frameworks=args.add_framework)
        print("--")
        print("Project {} updated".format(filename))

    def build_info(self):
        ctx = Context()
        print("Build Context")
        print("-------------")
        for attr in dir(ctx):
            if not attr.startswith("_"):
                if not callable(attr) and attr != 'supported_platforms':
                    print("{}: {}".format(attr, pformat(getattr(ctx, attr))))
        for supported_platform in ctx.supported_platforms:
            ul = '-' * (len(str(supported_platform)) + 6)
            print("\narch: {}\n{}".format(str(supported_platform), ul))
            for attr in dir(supported_platform):
                if not attr.startswith("_"):
                    if not callable(attr) and attr not in ['arch', 'ctx', 'get_env']:
                        print("{}: {}".format(attr, pformat(getattr(supported_platform, attr))))
            env = supported_platform.get_env()
            print("env ({}): {}".format(supported_platform, pformat(env)))

    def pip3(self):
        self.pip()

    def pip(self):
        _pip(sys.argv[2:])

    def launchimage(self):
        from .tools.external import xcassets
        self._xcassets("LaunchImage", xcassets.launchimage)

    def icon(self):
        from .tools.external import xcassets
        self._xcassets("Icon", xcassets.icon)

    def xcode(self):
        parser = argparse.ArgumentParser(description="Open the xcode project")
        parser.add_argument("filename", help="Path to your project or xcodeproj")
        args = parser.parse_args(sys.argv[2:])
        filename = self.find_xcodeproj(args.filename)
        sh.open(filename)

    def _xcassets(self, title, command):
        parser = argparse.ArgumentParser(
                description="Generate {} for your project".format(title))
        parser.add_argument("filename", help="Path to your project or xcodeproj")
        parser.add_argument("image", help="Path to your initial {}.png".format(title.lower()))
        args = parser.parse_args(sys.argv[2:])

        if not exists(args.image):
            logger.error("image path does not exists.")
            return

        filename = self.find_xcodeproj(args.filename)
        project_name = filename.split("/")[-1].replace(".xcodeproj", "")
        images_xcassets = realpath(join(filename, "..", project_name,
                                        "Images.xcassets"))
        if not exists(images_xcassets):
            logger.warning("Images.xcassets not found, creating it.")
            makedirs(images_xcassets)
        logger.info("Images.xcassets located at {}".format(images_xcassets))

        command(images_xcassets, args.image)


def main():
    ToolchainCL()


if __name__ == "__main__":
    main()
