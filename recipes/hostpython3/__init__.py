from toolchain import Recipe, shprint, ensure_dir
from os.path import join, exists
import os
import sh
import shutil
import logging

logger = logging.getLogger(__name__)


class Hostpython3Recipe(Recipe):
    version = "3.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    depends = []
    optional_depends = ["openssl"]
    archs = ["x86_64"]

    def init_with_ctx(self, ctx):
        super(Hostpython3Recipe, self).init_with_ctx(ctx)
        self.set_hostpython(self, "3.7")
        self.ctx.so_suffix = ".cpython-37m-darwin.so"
        self.ctx.hostpython = join(self.ctx.dist_dir, "hostpython3", "bin", "python")
        self.ctx.hostpgen = join(self.ctx.dist_dir, "hostpython3", "bin", "pgen")
        logger.info("Global: hostpython located at {}".format(self.ctx.hostpython))
        logger.info("Global: hostpgen located at {}".format(self.ctx.hostpgen))

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        # self.apply_patch("ssize-t-max.patch")
        # self.apply_patch("dynload.patch")
        # self.apply_patch("static-_sqlite3.patch")
        # shutil.copy("Modules/Setup.dist", "Modules/Setup")
        # if "openssl.build_all" in self.ctx.state:
        #     self.append_file("ModulesSetup.openssl", "Modules/Setup.local")
        self.set_marker("patched")

    def postbuild_arch(self, arch):
        return
        """
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
        """

    def get_build_env(self):
        sdk_path = sh.xcrun("--sdk", "macosx", "--show-sdk-path").strip()
        build_env = self.ctx.env.copy()
        self.build_env_x86_84 = build_env
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
        return build_env

    def build_x86_64(self):
        build_env = self.get_build_env()
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "--prefix={}".format(join(self.ctx.dist_dir, "hostpython3")),
                # "--disable-toolbox-glue",
                # "--without-gcc",
                _env=build_env)
        shprint(sh.make, "-C", self.build_dir, self.ctx.concurrent_make,
                _env=build_env)
        # shutil.move("python", "hostpython")
        # shutil.move("Parser/pgen", "Parser/hostpgen")

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = self.get_build_env()
        build_dir = self.get_build_dir(arch.arch)
        build_env["PATH"] = os.environ["PATH"]
        # Compiling sometimes looks for Python-ast.py in the 'Python' i.s.o.
        # the 'hostpython' folder. Create a symlink to fix. See issue #201
        # shprint(sh.ln, "-s",
        #         join(build_dir, "hostpython3"),
        #         join(build_dir, "Python"))
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_dir,
                "install",
                _env=build_env)
        # pylib_dir = join(self.ctx.dist_dir, "hostpython3", "lib", "python3.7")
        # if exists(pylib_dir):
        #     shutil.rmtree(pylib_dir)
        # shutil.copytree(
        #     join(build_dir, "Lib"),
        #     pylib_dir)
        # ensure_dir(join(pylib_dir, "config"))
        # shutil.copy(
        #     join(build_dir, "Makefile"),
        #     join(pylib_dir, "config", "Makefile"))
        shutil.copy(
            join(self.ctx.dist_dir, "hostpython3", "bin", "python3"),
            join(self.ctx.dist_dir, "hostpython3", "bin", "python"))


recipe = Hostpython3Recipe()
