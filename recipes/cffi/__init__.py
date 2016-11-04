from os.path import join
from toolchain import CythonRecipe
from toolchain import shprint
import os
import sh


class CffiRecipe(CythonRecipe):
    name = "cffi"
    version = "1.8.3"
    url = (
        "https://pypi.python.org/packages/0a/f3/"
        "686af8873b70028fccf67b15c78fd4e4667a3da995007afc71e786d61b0a/"
        "cffi-{version}.tar.gz"
    )
    library = "libcffi.a"
    depends = ["libffi", "host_setuptools", "pycparser"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(CffiRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        return env

    def install(self):
        arch = [arch for arch in self.filtered_archs if arch.arch == 'x86_64'][0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        # manually create expected directory in build directory
        scripts_dir = join("build", "scripts-2.7")
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir)
        hostpython = sh.Command(self.ctx.hostpython)

        # install cffi in hostpython
        #
        # XXX: installs, module import works, but FFI fails to instanciate:
        #
        # myhost:kivy-ios user$ ./dist/hostpython/bin/python
        # Could not find platform dependent libraries <exec_prefix>
        # Consider setting $PYTHONHOME to <prefix>[:<exec_prefix>]
        # Python 2.7.1 (r271:86832, Nov  4 2016, 10:41:44)
        # [GCC 4.2.1 Compatible Apple LLVM 7.3.0 (clang-703.0.31)] on darwin
        # Type "help", "copyright", "credits" or "license" for more information.
        # >>> import cffi
        # >>> cffi.api.FFI()
        # Traceback (most recent call last):
        #   File "<stdin>", line 1, in <module>
        #   File "/.../kivy-ios/dist/hostpython/lib/python2.7/site-packages/cffi/api.py", line 56, in __init__
        #     import _cffi_backend as backend
        # ImportError: dynamic module does not define init function (init_cffi_backend)
        r = self.get_recipe('hostlibffi', self.ctx)
        build_env = r.get_recipe_env(arch)
        args = [hostpython, "setup.py", "install"]
        shprint(*args, _env=build_env)

        # install cffi in root site packages
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        pythonpath = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        build_env['PYTHONPATH'] = pythonpath
        args = [hostpython, "setup.py", "install", "--prefix", dest_dir]
        shprint(*args, _env=build_env)

recipe = CffiRecipe()
