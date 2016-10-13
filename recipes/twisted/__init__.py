from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class TwistedRecipe(PythonRecipe):
    version = "16.1.1"
    url = "https://github.com/twisted/twisted/archive/twisted-{version}.zip"
    depends = ["python", "zope_interface", "openssl"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = os.path.join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = TwistedRecipe()
