# pure-python package, this can be removed when we'll support any python package
import os
import sh
from kivy_ios.toolchain import PythonRecipe, shprint


class PyYamlRecipe(PythonRecipe):
    version = "3.11"
    url = "https://pypi.python.org/packages/source/P/PyYAML/PyYAML-{version}.tar.gz"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = os.path.join(dest_dir, 'lib', 'python3.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = PyYamlRecipe()
