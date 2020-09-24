from kivy_ios.toolchain import CythonRecipe, shprint
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
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.8', 'site-packages')
        shprint(hostpython, "setup.py", "build_ext", _env=build_env)
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)
        
        # hack: copy _cffi_backend.so from hostpython
        so_file = "_cffi_backend.so"
        egg_name = "cffi-1.11.5-py2.7-macosx-10.4-x86_64.egg" # harded - needs to change
        dest_dir = join(self.ctx.dist_dir, "root", "python", "lib", "python2.7", "site-packages", egg_name)
        src_dir = join(self.ctx.dist_dir, "hostpython", "lib", "python2.7", "site-packages", egg_name)
        sh.cp(join(src_dir, so_file), join(dest_dir, so_file))


recipe = CffiRecipe()
