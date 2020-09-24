from os.path import join
from kivy_ios.toolchain import CythonRecipe, PythonRecipe, Recipe
from kivy_ios.toolchain import shprint
import os
import sh


class CryptographyRecipe(CythonRecipe):
    name = "cryptography"
    version = "2.2.2"
    url = "https://pypi.python.org/packages/source/c/cryptography/cryptography-{version}.tar.gz"
    library = "libcryptography.a"
    depends = ["host_setuptools", "host_cffi", "setuptools", "asn1crypto",
              "cffi", "enum34", "idna", "ipaddress", "six"]
    cythonize = False
    
    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("getentropy.patch")
        self.apply_patch("osrandom.patch")
        self.set_marker("patched")

    def get_recipe_env(self, arch):
        env = super(CryptographyRecipe, self).get_recipe_env(arch)
        r = self.get_recipe('openssl', self.ctx)
        openssl_dir = r.get_build_dir(arch.arch)
        target_python = Recipe.get_recipe('python', self.ctx).get_build_dir(arch.arch)
        
        env['PYTHON_ROOT'] = join(self.ctx.dist_dir, "root", "python")
        env["CC"] = "clang -Qunused-arguments -fcolor-diagnostics"
        env['CFLAGS'] += ' -I' + env['PYTHON_ROOT'] + '/include/python2.7' + \
                         ' -I' + join(openssl_dir, 'include') + \
                         ' -I' + join(self.ctx.dist_dir, "include", arch.arch, "libffi")
        env['LDFLAGS'] += ' -L' + env['PYTHON_ROOT'] + '/lib' + \
                          ' -L' + openssl_dir + \
                          ' -lpython2.7' + \
                          ' -lssl' + r.version + \
                          ' -lcrypto' + r.version
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
        pythonpath = join(dest_dir, 'lib', 'python3.8', 'site-packages')
        build_env['PYTHONPATH'] = pythonpath
        args = [hostpython, "setup.py", "install", "--prefix", dest_dir]
        shprint(*args, _env=build_env)

recipe = CryptographyRecipe()
