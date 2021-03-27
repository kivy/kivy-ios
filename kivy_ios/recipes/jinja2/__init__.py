# pure-python package, this can be removed when we'll support any python package
from kivy_ios.toolchain import PythonRecipe, shprint
from os.path import join
import sh
import os


class Jinja2Recipe(PythonRecipe):
    version = "2.11.2"
    url = "https://github.com/mitsuhiko/jinja2/archive/{version}.zip"
    depends = ["python", "markupsafe"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = self.ctx.site_packages_dir
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = Jinja2Recipe()
