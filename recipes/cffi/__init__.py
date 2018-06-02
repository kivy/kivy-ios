from toolchain import CythonRecipe, shprint
from os.path import join
import os
import sh


class CffiRecipe(CythonRecipe):
    name = "cffi"
    version = "1.11.5"
    url = "https://pypi.python.org/packages/source/c/cffi/cffi-{version}.tar.gz"
    library = "libcffi.a"
    depends = ["host_cffi", "libffi", "setuptools", "pycparser"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(CffiRecipe, self).get_recipe_env(arch)
        env["CFLAGS"] += " -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        env["LDFLAGS"] = " ".join([
            env.get('CFLAGS', '')
        ])
        return env

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        
         # manually create expected directory in build directory
        scripts_dir = join("build", "scripts-2.7")
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
        
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "build_ext", _env=build_env)
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = CffiRecipe()
