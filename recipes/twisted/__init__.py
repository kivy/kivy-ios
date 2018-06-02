from toolchain import CythonRecipe, shprint
from os.path import join
import os
import sh


class TwistedRecipe(CythonRecipe):
    name = "twisted"
    version = "16.6.0"
    url = "https://github.com/twisted/twisted/archive/twisted-{version}.tar.gz"
    library = "libtwisted.a"
    depends = ["python", "setuptools", "constantly", "incremental", "zope_interface"]
    optional_depends = ["pyopenssl"]
    cythonize = False
    
    def prebuild_arch(self, arch):
        if  self.has_marker("patched"):
            return
        self.apply_patch("remove_portmap_extension.patch")
        
        self.set_marker("patched")

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = TwistedRecipe()
