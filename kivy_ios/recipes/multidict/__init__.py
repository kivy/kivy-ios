# pure-python package, this can be removed when we'll support any python package
import os
import sh
from kivy_ios.toolchain import PythonRecipe, shprint


class MultidictRecipe(PythonRecipe):
    version = "4.5.2"
    url = "https://pypi.python.org/packages/source/m/multidict/multidict-{version}.tar.gz"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = os.path.join(dest_dir, 'lib', 'python3.8', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = MultidictRecipe()
