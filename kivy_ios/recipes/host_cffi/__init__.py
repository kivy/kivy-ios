from os.path import join
from kivy_ios.toolchain import Recipe, shprint
import os
import sh

libffi_tpl = """
prefix=%PREFIX%
exec_prefix=${prefix}
libdir=${exec_prefix}/build/Release
includedir=${libdir}/build_macosx-x86_64/include

Name: libffi
Description: Library supporting Foreign Function Interfaces
Version: %VERSION%
Libs: -L${libdir} -lffi
Cflags: -I${includedir}
"""

class HostCffiRecipe(Recipe):
    name = "host_cffi"
    version = "1.14.3"
    archs = ["x86_64"]
    url = "https://pypi.python.org/packages/source/c/cffi/cffi-{version}.tar.gz"
    depends = ["hostlibffi", "pycparser"]

    def get_recipe_env(self, arch):
        sdk_path = sh.xcrun("--sdk", "macosx", "--show-sdk-path").strip()
        env = super(HostCffiRecipe, self).get_recipe_env(arch)
        env["CC"] = "clang -Qunused-arguments -fcolor-diagnostics"
        env["LDFLAGS"] = " ".join([
                "-undefined dynamic_lookup",
                #"-shared",
                "-L{}".format(join(self.ctx.dist_dir, "hostlibffi", "usr", "local", "lib"))
                ])
        env["CFLAGS"] = " ".join([
                "--sysroot={}".format(sdk_path),
                "-I{}".format(join(self.ctx.dist_dir, "hostlibffi", "usr", "local", "include"))
                ])
        return env

    def prebuild_arch(self, arch):
        hostpython = sh.Command(self.ctx.hostpython)
        build_dir = self.get_build_dir(arch.arch)
        build_env = self.get_recipe_env(arch)
        os.chdir(build_dir)

        # generate a fake libffi pkg-config to let cffi use it
        hostlibffi = Recipe.get_recipe("hostlibffi", self.ctx)
        with open("libffi.pc", "w") as fd:
            tpl = libffi_tpl.replace("%PREFIX%",
                    hostlibffi.get_build_dir(arch.arch))
            tpl = tpl.replace("%VERSION%", hostlibffi.version)
            fd.write(tpl)

        build_env["PKG_CONFIG"] = "/usr/local/bin/pkg-config"
        build_env["PKG_CONFIG_PATH"] = build_dir 

        shprint(hostpython, "setup.py", "build_ext", _env=build_env)
        shprint(hostpython, "setup.py", "install", _env=build_env)

recipe = HostCffiRecipe()
