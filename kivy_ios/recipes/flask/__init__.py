# pure-python package, this can be removed when we'll support any python package
from kivy_ios.toolchain import PythonRecipe, shprint
from os.path import join
import sh
import os


class FlaskRecipe(PythonRecipe):
    version = "1.1.2"
    url = "https://github.com/mitsuhiko/flask/archive/{version}.zip"
    depends = ["python", "jinja2", "werkzeug", "itsdangerous", "click"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = self.ctx.site_packages_dir
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = FlaskRecipe()
