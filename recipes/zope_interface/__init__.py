from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class ZopeInterfaceRecipe(PythonRecipe):
    version = "4.3.2"
    url="https://github.com/zopefoundation/zope.interface/archive/{version}.zip"
    depends = ["python", "hostsetuptools"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = os.path.join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = ZopeInterfaceRecipe()
