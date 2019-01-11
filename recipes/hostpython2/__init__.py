from toolchain import Recipe, shprint, ensure_dir
from os.path import join, exists
import os
import sh
import shutil
import logging

logger = logging.getLogger(__name__)


class Hostpython2Recipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"
    depends = ["hostlibffi"]
    optional_depends = ["openssl"]
    archs = ["x86_64"]

    def init_with_ctx(self, ctx):
        super(Hostpython2Recipe, self).init_with_ctx(ctx)
        self.set_hostpython(self, "2.7")
        self.ctx.so_suffix = ".so"
        self.ctx.hostpython = join(self.ctx.dist_dir, "hostpython2", "bin", "python")
        self.ctx.hostpgen = join(self.ctx.dist_dir, "hostpython2", "bin", "pgen")
        logger.info("Global: hostpython located at {}".format(self.ctx.hostpython))
        logger.info("Global: hostpgen located at {}".format(self.ctx.hostpgen))

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.copy_file("_scproxy.py", "Lib/_scproxy.py")
        self.apply_patch("ssize-t-max.patch")
        self.apply_patch("dynload.patch")
        self.apply_patch("static-_sqlite3.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        if "openssl.build_all" in self.ctx.state:
            self.append_file("ModulesSetup.openssl", "Modules/Setup.local")
        self.set_marker("patched")

    def postbuild_arch(self, arch):
        makefile_fn = join(self.build_dir, "Makefile")
        with open(makefile_fn) as fd:
            lines = fd.readlines()
        for index, line in enumerate(lines):
            if "-bundle" not in line:
                continue
            parts = line.split(" ")
            parts.remove("-bundle")
            if "-bundle_loader" in parts:
                i = parts.index("-bundle_loader")
                parts.pop(i)
                parts.pop(i)
            lines[index] = " ".join(parts)
        with open(makefile_fn, "w") as fd:
            fd.writelines(lines)

    def build_x86_64(self):
        sdk_path = sh.xcrun("--sdk", "macosx", "--show-sdk-path").strip()
        build_env = self.ctx.env.copy()
        ccache = (build_env["CCACHE"] + ' ') if 'CCACHE' in build_env else ''
        build_env["CC"] = ccache + "clang -Qunused-arguments -fcolor-diagnostics"
        build_env["LDFLAGS"] = " ".join([
                "-lsqlite3",
                "-lffi",
                "-L{}".format(join(self.ctx.dist_dir, "hostlibffi", "usr", "local", "lib"))
                ])
        build_env["CFLAGS"] = " ".join([
                "--sysroot={}".format(sdk_path),
                "-arch x86_64",
                "-mmacosx-version-min=10.12",
                "-I{}".format(join(self.ctx.dist_dir, "hostlibffi", "usr", "local", "include"))
                ])

        if "openssl.build_all" in self.ctx.state:
            build_env["LDFLAGS"] += " -L{}".format(join(self.ctx.dist_dir, "lib"))
            build_env["CFLAGS"] += " -I{}".format(join(self.ctx.dist_dir, "include",
                                                       "x86_64", "openssl"))

        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "--prefix={}".format(join(self.ctx.dist_dir, "hostpython2")),
                "--disable-toolbox-glue",
                "--without-gcc",
                _env=build_env)
        shprint(sh.make, "-C", self.build_dir, self.ctx.concurrent_make, "python", "Parser/pgen",
                _env=build_env)
        shutil.move("python", "hostpython2")
        shutil.move("Parser/pgen", "Parser/hostpgen")

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = arch.get_env()
        build_dir = self.get_build_dir(arch.arch)
        build_env["PATH"] = os.environ["PATH"]
        # Compiling sometimes looks for Python-ast.py in the 'Python' i.s.o.
        # the 'hostpython' folder. Create a symlink to fix. See issue #201
        shprint(sh.ln, "-s",
                join(build_dir, "hostpython2"),
                join(build_dir, "Python"))
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_dir,
                "bininstall", "inclinstall",
                _env=build_env)
        pylib_dir = join(self.ctx.dist_dir, "hostpython2", "lib", "python2.7")
        if exists(pylib_dir):
            shutil.rmtree(pylib_dir)
        shutil.copytree(
            join(build_dir, "Lib"),
            pylib_dir)
        ensure_dir(join(pylib_dir, "config"))
        shutil.copy(
            join(build_dir, "Makefile"),
            join(pylib_dir, "config", "Makefile"))
        shutil.copy(
            join(build_dir, "Parser", "pgen"),
            join(self.ctx.dist_dir, "hostpython2", "bin", "pgen"))


recipe = Hostpython2Recipe()
