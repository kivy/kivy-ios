from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class AutobahnRecipe(PythonRecipe):
    version = "0.16.0"
    url = "https://github.com/crossbario/autobahn-python/archive/v{version}.zip"
    #depends = ["python", "setuptools", "zope_interface", "twisted"]
    depends = ["python", "setuptools", "zope_interface", "twisted"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = os.path.join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = AutobahnRecipe()
