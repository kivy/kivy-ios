from toolchain import Recipe, shprint
from os.path import join
import sh
import shutil


class PythonRecipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"
    depends = ["libffi", ]

    def download(self):
        super(PythonRecipe, self).download()
        self.ctx.hostpython = join(
                self.ctx.build_dir, "i386", self.archive_root,
                "hostpython")
        self.ctx.hostpgen = join(
                self.ctx.build_dir, "i386", self.archive_root,
                "Parser", "hostpgen")
        print("Global: hostpython located at {}".format(self.ctx.hostpython))
        print("Global: hostpgen located at {}".format(self.ctx.hostpgen))

    def prebuild_arch(self, arch):
        # common to all archs
        if  self.has_marker("patched"):
            return
        self.apply_patch("ssize-t-max.patch")
        self.apply_patch("dynload.patch")
        self.apply_patch("static-_sqlite3.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.copy_file("_scproxy.py", "Lib/_scproxy.py")
        #self.copy_file("Setup.dist", "Modules/Setup.dist")

        if arch in ("armv7", "armv7s", "arm64"):
            self.apply_patch("xcompile.patch")
            self.apply_patch("setuppath.patch")
            self.append_file("ModulesSetup.mobile", "Modules/Setup.local")

        self.set_marker("patched")

    def build_i386(self):
        sdk_path = sh.xcrun(
            "--sdk", "macosx",
            "--show-sdk-path").splitlines()[0]

        build_env = self.ctx.env.copy()
        build_env["CC"] = "clang -Qunused-arguments -fcolor-diagnostics"
        build_env["LDFLAGS"] = "-lsqlite3"
        build_env["CFLAGS"] = "--sysroot={}".format(sdk_path)
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure, _env=build_env)
        shprint(sh.make, "-C", self.build_dir, "-j4", "python.exe", "Parser/pgen",
                _env=build_env)
        shutil.move("python.exe", "hostpython")
        shutil.move("Parser/pgen", "Parser/hostpgen")

    def build_arch(self, arch):
        if self.has_marker("build"):
            return
        if arch == "i386":
            super(PythonRecipe, self).build_arch(arch)
            self.set_marker("build")
            return

        build_env = self.ctx.env.copy()

        build_env["CC"] = sh.xcrun("-find", "-sdk", "iphoneos", "clang").splitlines()[0]
        build_env["AR"] = sh.xcrun("-find", "-sdk", "iphoneos", "ar").splitlines()[0]
        build_env["LD"] = sh.xcrun("-find", "-sdk", "iphoneos", "ld").splitlines()[0]
        build_env["CFLAGS"] = " ".join([
            "-arch", arch,
            "-pipe", "-no-cpp-precomp",
            "-isysroot", self.ctx.iossdkroot,
            "-O3",
            "-miphoneos-version-min={}".format(self.ctx.sdkver)])
        build_env["LDFLAGS"] = " ".join([
            "-arch", arch,
            "-undefined dynamic_lookup",
            "-Lextralibs/",
            "-lsqlite3",
            "-isysroot", self.ctx.iossdkroot])

        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={}".format(build_env["LDFLAGS"]),
                "--without-pymalloc",
                "--disable-toolbox-glue",
                "--host={}-apple-darwin".format(arch),
                "--prefix=/python",
                "--without-doc-strings",
                _env=build_env)
        self.apply_patch("pyconfig.patch")
        self.apply_patch("ctypes_duplicate.patch")

        shprint(sh.make, "-j4",
                "CROSS_COMPILE_TARGET=yes",
                "HOSTPYTHON={}".format(self.ctx.hostpython),
                "HOSTPGEN={}".format(self.ctx.hostpgen))


recipe = PythonRecipe()
