"""
Tool for compiling iOS toolchain
================================

This tool intend to replace all the previous tools/ in shell script.
"""

import sys
from sys import stdout
from os.path import join, dirname, realpath, exists, isdir, basename
from os import listdir, unlink, makedirs, environ
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
    #kwargs["_err_to_out"] = True
    for line in command(*args, **kwargs):
        stdout.write(line)


class ChromeDownloader(FancyURLopener):
    version = (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36')

urlretrieve = ChromeDownloader().retrieve


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
            iphoneos = iphoneos[0].split()[-1]
            self.sdkver = iphoneos

        # get the latest iphonesimulator version
        iphonesim = [x for x in sdks if "iphonesimulator" in x]
        if not iphoneos:
            ok = False
            print("Error: No iphonesimulator SDK installed")
        else:
            iphonesim = iphonesim[0].split()[-1]
            self.sdksimver = iphonesim

        # get the path for Developer
        self.devroot = "{}/Platforms/iPhoneOS.platform/Developer".format(
            sh.xcode_select("-print-path").strip())

        # path to the iOS SDK
        self.iossdkroot = "{}/SDKs.iPhoneOS{}.sdk".format(
            self.devroot, self.sdkver)

        # root of the toolchain
        self.root_dir = realpath(dirname(__file__))
        self.build_dir = "{}/build".format(self.root_dir)
        self.cache_dir = "{}/.cache".format(self.root_dir)
        self.dist_dir = "{}/dist".format(self.root_dir)
        self.install_dir = "{}/dist/root".format(self.root_dir)
        self.archs = ("i386", "armv7", "armv7s", "arm64")

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


class Recipe(object):
    version = None
    url = None

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
        filename = join(self.recipe_dir, filename)
        dest = join(self.build_dir, dest)
        shutil.copy(filename, dest)

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

    def marker(self, marker):
        """
        Return a context that will be executed only if the marker has been set
        """

    @property
    def name(self):
        modname = self.__class__.__module__
        return modname.split(".", 1)[-1]

    @property
    def archive_fn(self):
        if hasattr(self, "ext"):
            ext = self.ext
        else:
            ext = basename(self.url).split(".", 1)[-1]
        fn = "{}/{}.{}".format(
            self.ctx.cache_dir,
            self.name, ext)
        return fn

    # Public Recipe API to be subclassed if needed

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

    def extract(self):
        # recipe tmp directory
        archive_root = self.get_archive_rootdir(self.archive_fn)
        for arch in self.ctx.archs:
            print("Extract {} for {}".format(self.name, arch))
            build_dir = join(self.ctx.build_dir, arch)
            if exists(join(build_dir, archive_root)):
                continue
            ensure_dir(build_dir)
            self.extract_file(self.archive_fn, build_dir) 

    def build_all(self):
        archive_root = self.get_archive_rootdir(self.archive_fn)
        for arch in self.ctx.archs:
            self.build_dir = join(self.ctx.build_dir, arch, archive_root)
            self.prebuild_arch(arch)
            self.build_arch(arch)
            self.postbuild_arch(arch)

    def prebuild_arch(self, arch):
        print("Prebuild {} for {}".format(self.name, arch))
        prebuild = "prebuild_{}".format(arch)
        if hasattr(self, prebuild):
            getattr(self, prebuild)()

    def build_arch(self, arch):
        print("Build {} for {}".format(self.name, arch))
        build = "build_{}".format(arch)
        if hasattr(self, build):
            getattr(self, build)()

    def postbuild_arch(self, arch):
        print("Postbuild {} for {}".format(self.name, arch))
        postbuild = "postbuild_{}".format(arch)
        if hasattr(self, postbuild):
            getattr(self, postbuild)()


def list_recipes():
    recipes_dir = join(dirname(__file__), "recipes")
    for name in listdir(recipes_dir):
        fn = join(recipes_dir, name)
        if isdir(fn):
            yield name

def compile_recipe(name, ctx):
    mod = importlib.import_module("recipes.{}".format(name))
    recipe = mod.recipe
    recipe.recipe_dir = join(ctx.root_dir, "recipes", name)
    recipe.ctx = ctx
    recipe.execute()


def ensure_dir(filename):
    if not exists(filename):
        makedirs(filename)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Compile Python and others extensions for iOS')
    args = parser.parse_args()
    ctx = Context()
    print list(list_recipes())
    compile_recipe("hostpython", ctx)
