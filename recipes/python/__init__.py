from toolchain import Recipe, shprint
from os.path import join
import sh


class PythonRecipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"
    depends = ["hostpython", "libffi", ]

    def prebuild_arch(self, arch):
        # common to all archs
        if  self.has_marker("patched"):
            return
        self.apply_patch("ssize-t-max.patch")
        self.apply_patch("dynload.patch")
        self.apply_patch("static-_sqlite3.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.copy_file("_scproxy.py", "Lib/_scproxy.py")
        self.apply_patch("xcompile.patch")
        self.apply_patch("setuppath.patch")
        self.append_file("ModulesSetup.mobile", "Modules/Setup.local")

        self.set_marker("patched")

    def build_arch(self, arch):
        build_env = self.ctx.env.copy()

        build_env["CC"] = sh.xcrun("-find", "-sdk", arch.sdk, "clang").strip()
        build_env["AR"] = sh.xcrun("-find", "-sdk", arch.sdk, "ar").strip()
        build_env["LD"] = sh.xcrun("-find", "-sdk", arch.sdk, "ld").strip()
        build_env["CFLAGS"] = " ".join([
            "-arch", arch.arch,
            "-pipe", "-no-cpp-precomp",
            "-isysroot", arch.sysroot,
            "-O3",
            "-miphoneos-version-min={}".format(arch.version_min)])
        build_env["LDFLAGS"] = " ".join([
            "-arch", arch.arch,
            "-undefined dynamic_lookup",
            "-Lextralibs/",
            "-lsqlite3",
            "-isysroot", arch.sysroot])

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
