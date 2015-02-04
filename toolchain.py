"""
Tool for compiling iOS toolchain
================================

This tool intend to replace all the previous tools/ in shell script.
"""

import sys
from sys import stdout
from os.path import join, dirname, realpath, exists, isdir, basename
from os import listdir, unlink, makedirs, environ, chdir
import zipfile
import tarfile
import importlib
import sh
import shutil
try:
    from urllib.request import FancyURLopener
except ImportError:
    from urllib import FancyURLopener


def shprint(command, *args, **kwargs):
    kwargs["_iter"] = True
    kwargs["_out_bufsize"] = 1
    kwargs["_err_to_out"] = True
    #kwargs["_err_to_out"] = True
    for line in command(*args, **kwargs):
        stdout.write(line)


class ChromeDownloader(FancyURLopener):
    version = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')

urlretrieve = ChromeDownloader().retrieve


class Arch(object):
    def __init__(self, ctx):
        super(Arch, self).__init__()
        self.ctx = ctx

    def get_env(self):
        env = {}
        env["CC"] = sh.xcrun("-find", "-sdk", self.sdk, "clang").strip()
        env["AR"] = sh.xcrun("-find", "-sdk", self.sdk, "ar").strip()
        env["LD"] = sh.xcrun("-find", "-sdk", self.sdk, "ld").strip()
        env["CFLAGS"] = " ".join([
            "-arch", self.arch,
            "-pipe", "-no-cpp-precomp",
            "--sysroot={}".format(self.sysroot),
            "-I{}/include/{}".format(self.ctx.dist_dir, self.arch),
            "-O3",
            self.version_min
        ])
        env["LDFLAGS"] = " ".join([
            "-arch", self.arch,
            "--sysroot={}".format(self.sysroot),
            "-L{}/{}".format(self.ctx.dist_dir, "lib"),
            "-lsqlite3",
            "-undefined", "dynamic_lookup",
            self.version_min
        ])
        return env



class ArchSimulator(Arch):
    sdk = "iphonesimulator"
    arch = "i386"
    triple = "i386-apple-darwin11"
    version_min = "-miphoneos-version-min=6.0.0"
    sysroot = sh.xcrun("--sdk", "iphonesimulator", "--show-sdk-path").strip()


class Arch64Simulator(Arch):
    sdk = "iphonesimulator"
    arch = "x86_64"
    triple = "x86_64-apple-darwin13"
    version_min = "-miphoneos-version-min=7.0"
    sysroot = sh.xcrun("--sdk", "iphonesimulator", "--show-sdk-path").strip()


class ArchIOS(Arch):
    sdk = "iphoneos"
    arch = "armv7"
    triple = "arm-apple-darwin11"
    version_min = "-miphoneos-version-min=6.0.0"
    sysroot = sh.xcrun("--sdk", "iphoneos", "--show-sdk-path").strip()


class Arch64IOS(Arch):
    sdk = "iphoneos"
    arch = "arm64"
    triple = "aarch64-apple-darwin13"
    version_min = "-miphoneos-version-min=7.0"
    sysroot = sh.xcrun("--sdk", "iphoneos", "--show-sdk-path").strip()
    

class Graph(object):
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
            leftmost = [l for l, s in graph.items() if not s]
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


class Context(object):
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

    def __init__(self):
        super(Context, self).__init__()
        ok = True

        sdks = sh.xcodebuild("-showsdks").splitlines()

        # get the latest iphoneos
        iphoneos = [x for x in sdks if "iphoneos" in x]
        if not iphoneos:
            print("No iphone SDK installed")
            ok = False
        else:
            iphoneos = iphoneos[0].split()[-1].replace("iphoneos", "")
            self.sdkver = iphoneos

        # get the latest iphonesimulator version
        iphonesim = [x for x in sdks if "iphonesimulator" in x]
        if not iphoneos:
            ok = False
            print("Error: No iphonesimulator SDK installed")
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
        self.build_dir = "{}/build".format(self.root_dir)
        self.cache_dir = "{}/.cache".format(self.root_dir)
        self.dist_dir = "{}/dist".format(self.root_dir)
        self.install_dir = "{}/dist/root".format(self.root_dir)
        self.include_dir = "{}/dist/include".format(self.root_dir)
        self.archs = (
            ArchSimulator(self),
            Arch64Simulator(self),
            ArchIOS(self),
            Arch64IOS(self))

        # path to some tools
        self.ccache = sh.which("ccache")
        if not self.ccache:
            print("ccache is missing, the build will not be optimized in the future.")
        for cython_fn in ("cython-2.7", "cython"):
            cython = sh.which(cython_fn)
            if cython:
                self.cython = cython
                break
        if not self.cython:
            ok = False
            print("Missing requirement: cython is not installed")

        # check the basic tools
        for tool in ("pkg-config", "autoconf", "automake", "libtool", "hg"):
            if not sh.which(tool):
                print("Missing requirement: {} is not installed".format(
                    tool))

        if not ok:
            sys.exit(1)

        ensure_dir(self.root_dir)
        ensure_dir(self.build_dir)
        ensure_dir(self.cache_dir)
        ensure_dir(self.dist_dir)
        ensure_dir(self.install_dir)
        ensure_dir(self.include_dir)
        ensure_dir(join(self.include_dir, "common"))

        # remove the most obvious flags that can break the compilation
        self.env.pop("MACOSX_DEPLOYMENT_TARGET", None)
        self.env.pop("PYTHONDONTWRITEBYTECODE", None)
        self.env.pop("ARCHFLAGS", None)
        self.env.pop("CFLAGS", None)
        self.env.pop("LDFLAGS", None)


class Recipe(object):
    version = None
    url = None
    archs = []
    depends = []
    library = None

    # API available for recipes
    def download_file(self, url, filename, cwd=None):
        """
        Download an `url` to `outfn`
        """
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
        if exists(filename):
            unlink(filename)

        print('Downloading {0}'.format(url))
        urlretrieve(url, filename, report_hook)
        return filename

    def extract_file(self, filename, cwd):
        """
        Extract the `filename` into the directory `cwd`.
        """
        print("Extract {} into {}".format(filename, cwd))
        if filename.endswith(".tgz") or filename.endswith(".tar.gz"):
            shprint(sh.tar, "-C", cwd, "-xvzf", filename)

        elif filename.endswith(".tbz2") or filename.endswith(".tar.bz2"):
            shprint(sh.tar, "-C", cwd, "-xvjf", filename)

        elif filename.endswith(".zip"):
            zf = zipfile.ZipFile(filename)
            zf.extractall(path=cwd)
            zf.close()

        else:
            print("Error: cannot extract, unreconized extension for {}".format(
                filename))
            raise Exception()

    def get_archive_rootdir(self, filename):
        if filename.endswith(".tgz") or filename.endswith(".tar.gz") or \
            filename.endswith(".tbz2") or filename.endswith(".tar.bz2"):
            archive = tarfile.open(filename)
            root = archive.next().path.split("/")
            return root[0]
        else:
            print("Error: cannot detect root direction")
            print("Unrecognized extension for {}".format(filename))
            raise Exception()

    def apply_patch(self, filename):
        """
        Apply a patch from the current recipe directory into the current
        build directory.
        """
        print("Apply patch {}".format(filename))
        filename = join(self.recipe_dir, filename)
        sh.patch("-t", "-d", self.build_dir, "-p1", "-i", filename)

    def copy_file(self, filename, dest):
        print("Copy {} to {}".format(filename, dest))
        filename = join(self.recipe_dir, filename)
        dest = join(self.build_dir, dest)
        shutil.copy(filename, dest)

    def append_file(self, filename, dest):
        print("Append {} to {}".format(filename, dest))
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
        try:
            unlink(join(self.build_dir, ".{}".format(marker)))
        except:
            pass

    @property
    def name(self):
        modname = self.__class__.__module__
        return modname.split(".", 1)[-1]

    @property
    def archive_fn(self):
        bfn = basename(self.url.format(version=self.version))
        fn = "{}/{}-{}".format(
            self.ctx.cache_dir,
            self.name, bfn)
        return fn

    @property
    def filtered_archs(self):
        for arch in self.ctx.archs:
            if not self.archs or (arch.arch in self.archs):
                yield arch

    def get_build_dir(self, arch):
        return join(self.ctx.build_dir, self.name, arch, self.archive_root)

    # Public Recipe API to be subclassed if needed

    def init_with_ctx(self, ctx):
        self.ctx = ctx

    def execute(self):
        print("Download {}".format(self.name))
        self.download()
        print("Extract {}".format(self.name))
        self.extract()
        print("Build {}".format(self.name))
        self.build_all()

    def download(self):
        fn = self.archive_fn
        if not exists(fn):
            self.download_file(self.url.format(version=self.version), fn)
        self.archive_root = self.get_archive_rootdir(self.archive_fn)

    def extract(self):
        # recipe tmp directory
        for arch in self.filtered_archs:
            print("Extract {} for {}".format(self.name, arch.arch))
            self.extract_arch(arch.arch)

    def extract_arch(self, arch):
        build_dir = join(self.ctx.build_dir, self.name, arch)
        if exists(join(build_dir, self.archive_root)):
            return
        ensure_dir(build_dir)
        self.extract_file(self.archive_fn, build_dir) 

    def build_all(self):
        filtered_archs = list(self.filtered_archs)
        print("Build {} for {} (filtered)".format(
            self.name,
            ", ".join([x.arch for x in filtered_archs])))
        for arch in self.filtered_archs:
            self.build_dir = self.get_build_dir(arch.arch)
            if self.has_marker("building"):
                print("Warning: {} build for {} has been incomplete".format(
                    self.name, arch.arch))
                print("Warning: deleting the build and restarting.")
                shutil.rmtree(self.build_dir)
                self.extract_arch(arch.arch)

            if self.has_marker("build_done"):
                print("Build python for {} already done.".format(arch.arch))
                continue

            self.set_marker("building")

            chdir(self.build_dir)
            print("Prebuild {} for {}".format(self.name, arch.arch))
            self.prebuild_arch(arch)
            print("Build {} for {}".format(self.name, arch.arch))
            self.build_arch(arch)
            print("Postbuild {} for {}".format(self.name, arch.arch))
            self.postbuild_arch(arch)
            self.delete_marker("building")
            self.set_marker("build_done")

        name = self.name
        if not name.startswith("lib"):
            name = "lib{}".format(name)
        static_fn = join(self.ctx.dist_dir, "lib", "{}.a".format(name))
        ensure_dir(dirname(static_fn))
        print("Lipo {} to {}".format(self.name, static_fn))
        self.make_lipo(static_fn)
        print("Install {}".format(self.name))
        self.install()

    def prebuild_arch(self, arch):
        prebuild = "prebuild_{}".format(arch.arch)
        if hasattr(self, prebuild):
            getattr(self, prebuild)()

    def build_arch(self, arch):
        build = "build_{}".format(arch.arch)
        if hasattr(self, build):
            getattr(self, build)()

    def postbuild_arch(self, arch):
        postbuild = "postbuild_{}".format(arch.arch)
        if hasattr(self, postbuild):
            getattr(self, postbuild)()

    def make_lipo(self, filename):
        if not self.library:
            return
        args = []
        for arch in self.filtered_archs:
            library = self.library.format(arch=arch)
            args += [
                "-arch", arch.arch,
                join(self.get_build_dir(arch.arch), library)]
        shprint(sh.lipo, "-create", "-output", filename, *args)

    def install(self):
        pass

    @classmethod
    def list_recipes(cls):
        recipes_dir = join(dirname(__file__), "recipes")
        for name in listdir(recipes_dir):
            fn = join(recipes_dir, name)
            if isdir(fn):
                yield name

    @classmethod
    def get_recipe(cls, name):
        if not hasattr(cls, "recipes"):
           cls.recipes = {}
        if name in cls.recipes:
            return cls.recipes[name]
        mod = importlib.import_module("recipes.{}".format(name))
        recipe = mod.recipe
        recipe.recipe_dir = join(ctx.root_dir, "recipes", name)
        return recipe


def build_recipes(names, ctx):
    # gather all the dependencies
    print("Want to build {}".format(names))
    graph = Graph()
    recipe_to_load = names
    recipe_loaded = []
    while names:
        name = recipe_to_load.pop(0)
        if name in recipe_loaded:
            continue
        print("Load recipe {}".format(name))
        recipe = Recipe.get_recipe(name)
        graph.add(name, name)
        print("Recipe {} depends of {}".format(name, recipe.depends))
        for depend in recipe.depends:
            graph.add(name, depend)
            recipe_to_load += recipe.depends
        recipe_loaded.append(name)

    build_order = list(graph.find_order())
    print("Build order is {}".format(build_order))
    for name in build_order:
        recipe = Recipe.get_recipe(name)
        recipe.init_with_ctx(ctx)
        recipe.execute()

def ensure_dir(filename):
    if not exists(filename):
        makedirs(filename)


if __name__ == "__main__":
    #import argparse
    #parser = argparse.ArgumentParser(
    #    description='Compile Python and others extensions for iOS')
    #args = parser.parse_args()
    ctx = Context()
    build_recipes(sys.argv[1:], ctx)
