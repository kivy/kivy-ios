from os.path import join
from toolchain import PythonRecipe
from toolchain import shprint
import os
import sh


class IPAddressRecipe(PythonRecipe):
    version = "1.0.17"
    url = (
        "https://pypi.python.org/packages/bb/26/"
        "3b64955ff73f9e3155079b9ed31812afdfa5333b5c76387454d651ef593a/"
        "ipaddress-{version}.tar.gz"
    )
    depends = ["python"]

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

recipe = IPAddressRecipe()
