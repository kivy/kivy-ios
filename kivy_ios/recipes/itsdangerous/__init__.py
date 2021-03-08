# pure-python package, this can be removed when we'll support any python package
from kivy_ios.toolchain import PythonRecipe, shprint
from kivy_ios.context_managers import cd
from os.path import join
import sh


class ItsDangerousRecipe(PythonRecipe):
    version = "1.1.0"
    url = "https://github.com/mitsuhiko/itsdangerous/archive/{version}.zip"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = self.ctx.site_packages_dir
        with cd(build_dir):
            shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = ItsDangerousRecipe()
