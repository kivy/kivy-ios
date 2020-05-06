from kivy_ios.toolchain import Recipe, cd, shprint
from os.path import join
import os
import sh
import shutil
import logging

logger = logging.getLogger(__name__)


class Hostpython3Recipe(Recipe):
    version = "3.8.2"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    depends = ["hostlibffi", "hostopenssl"]
    optional_depends = []
    archs = ["x86_64"]
    build_subdir = 'native-build'

    def init_with_ctx(self, ctx):
        super().init_with_ctx(ctx)
        self.set_hostpython(self, "3.8")
        self.ctx.so_suffix = ".cpython-38m-darwin.so"
        self.ctx.hostpython = join(self.ctx.dist_dir, "hostpython3", "bin", "python")
        self.ctx.hostpgen = join(self.ctx.dist_dir, "hostpython3", "bin", "pgen")
        logger.info("Global: hostpython located at {}".format(self.ctx.hostpython))
        logger.info("Global: hostpgen located at {}".format(self.ctx.hostpgen))

    def get_build_subdir(self, arch):
        return join(self.get_build_dir(arch), self.build_subdir)

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("pyconfig_detection.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.set_marker("patched")

    def postbuild_arch(self, arch):
        return

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
        return build_env

    def build_x86_64(self):
        build_env = self.get_build_env()
        configure = sh.Command(join(self.build_dir, "configure"))
        arch = self.filtered_archs[0]
        build_subdir = self.get_build_subdir(arch.arch)
        os.makedirs(build_subdir, exist_ok=True)
        with cd(build_subdir):
            shprint(configure,
                    "--prefix={}".format(join(self.ctx.dist_dir, "hostpython3")),
                    "--with-openssl={}".format(join(self.ctx.dist_dir, 'hostopenssl')),
                    _env=build_env)
        shprint(sh.make, "-C", build_subdir, self.ctx.concurrent_make,
                _env=build_env)

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_env = self.get_build_env()
        build_subdir = self.get_build_subdir(arch.arch)
        build_env["PATH"] = os.environ["PATH"]
        shprint(sh.make, self.ctx.concurrent_make,
                "-C", build_subdir,
                "install",
                _env=build_env)
        shutil.copy(
            join(self.ctx.dist_dir, "hostpython3", "bin", "python3"),
            join(self.ctx.dist_dir, "hostpython3", "bin", "python"))
        """
        I don't like this kind of "patches".
        sysconfig was overriding our cflags and extensions were failing to build.
        This hack resets the cflags provided by sysconfig.
        """
        with open(join(self.ctx.dist_dir, "hostpython3", "lib", "python3.8", "distutils", "sysconfig.py"), 'r') as sysconfigfile:
            lines = sysconfigfile.readlines()
        lines[192] = '        cflags = ""\n'
        with open(join(self.ctx.dist_dir, "hostpython3", "lib", "python3.8", "distutils", "sysconfig.py"), 'w') as sysconfigfile:
            sysconfigfile.writelines(lines)


recipe = Hostpython3Recipe()
