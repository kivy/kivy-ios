from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class HostSetuptoolsRecipe(PythonRecipe):
    version = "28.0.0"
    url = "https://github.com/pypa/setuptools/archive/v{version}.zip"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = os.path.join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "bootstrap.py", _env=build_env)
        shprint(hostpython, "setup.py", "install", _env=build_env)

recipe = HostSetuptoolsRecipe()
