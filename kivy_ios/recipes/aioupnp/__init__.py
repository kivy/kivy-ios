# pure-python package, this can be removed when we'll support any python package
import os
import sh
from kivy_ios.toolchain import CythonRecipe, shprint
from os.path import join

class AioupnpRecipe(CythonRecipe):
    version = "0.0.17"
    url = "https://pypi.python.org/packages/source/a/aioupnp/aioupnp-{version}.tar.gz"
    depends = ["python", "defusedxml"]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("exclude_netifaces.patch")
        self.apply_patch("none_netifaces.patch")
        self.set_marker("patched")

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.8', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = AioupnpRecipe()
