from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class PyOpenSSLRecipe(PythonRecipe):
    version = "16.1.0"
    url = (
        "https://pypi.python.org/packages/15/1e/"
        "79c75db50e57350a7cefb70b110255757e9abd380a50ebdc0cfd853b7450/"
        "pyOpenSSL-{version}.tar.gz"
    )
    depends = ["openssl", "cryptography"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        pythonpath = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        build_env['PYTHONPATH'] = pythonpath
        args = [hostpython, "setup.py", "install", "--prefix", dest_dir]
        shprint(*args, _env=build_env)

recipe = PyOpenSSLRecipe()
