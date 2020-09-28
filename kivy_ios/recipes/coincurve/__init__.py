import sh
import os
from os.path import join

from kivy_ios.toolchain import CythonRecipe, Recipe, shprint
from kivy_ios.context_managers import cd


class CoincurveRecipe(CythonRecipe):
    version = "7.1.0"
    url = "https://github.com/ofek/coincurve/archive/{version}.tar.gz"
    depends = ["python3", "libffi", "cffi", "pycparser", "libsecp256k1"]
    library = 'libcoincurve.a'
    pre_build_ext = True
    include_per_arch = True
    
    def dest_dir(self):
        return join(self.ctx.dist_dir, "root", "python3")
    
    def prebuild_arch(self, arch):
        # common to all archs
        if self.has_marker("patched"):
            return
        self.apply_patch("cross_compile.patch")
        self.apply_patch("drop_setup_requires.patch")
        self.apply_patch("find_lib.patch")
        self.apply_patch("no-download.patch")
        self.apply_patch("setup.py.patch")
        self.set_marker("patched")
    
    def get_recipe_env(self, arch):
        env = arch.get_env()
        # sets linker to use the correct gcc (cross compiler)
        env['TOOLCHAIN_PREFIX'] = arch.triple
        env['LDSHARED'] = env['CC'] + ' -pthread -shared -Wl'
        libsecp256k1 = self.get_recipe('libsecp256k1', self.ctx)
        libsecp256k1_dir = libsecp256k1.get_build_dir(arch.arch)
        env['LDFLAGS'] += ' -L{}'.format(os.path.join(libsecp256k1_dir, '.libs'))
        env['CFLAGS'] += ' -I' + os.path.join(libsecp256k1_dir, 'include')
        
        target_python = Recipe.get_recipe('python3', self.ctx).get_build_dir(arch.arch)
        env['LDFLAGS'] += ' -L' + target_python
        
        print(env['LDFLAGS'])
        
        python_version = '3.8'
        env["PYTHONPATH"] = join(self.dest_dir(), "lib", "python3.8", "site-packages")
        env['PYTHON_ROOT'] = join(self.ctx.dist_dir, "root", "python3")
        env['CFLAGS'] += ' -I' + env['PYTHON_ROOT'] + '/include/python{}'.format(python_version)
        env['LDFLAGS'] += " -lpython{}".format(python_version)
        env['LDFLAGS'] += " -lsecp256k1 -lssl -lcrypto -lffi -lz"
        return env

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.8', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)
        
    def postbuild_arch(self, arch):
        py_arch = arch.arch
        if py_arch == "arm64":
            py_arch = "x86_64"
        build_dir = self.get_build_dir(arch.arch)
        build_env = self.get_recipe_env(arch)
        tmp_folder = 'build/temp.macosx-10.15-{}-3.8/build/temp.macosx-10.15-{}-3.8'.format(py_arch, py_arch)
        shprint(sh.Command(build_env['AR']),
                    "-q",
                    "{}/{}".format(self.build_dir, self.library),
                    "{}/{}/_libsecp256k1.o".format(self.build_dir, tmp_folder))

recipe = CoincurveRecipe()
