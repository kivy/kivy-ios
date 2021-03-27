# pure-python package, this can be removed when we'll support any python package
from kivy_ios.toolchain import PythonRecipe, shprint
from os.path import join
import sh
import os


class MarkupSafeRecipe(PythonRecipe):
    version = "1.1.1"
    url = "https://github.com/mitsuhiko/markupsafe/archive/{version}.zip"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = self.ctx.site_packages_dir
        cmd = sh.Command("sed")
        shprint(cmd, "-i", "", "s/,.*Feature//g", "./setup.py", _env=build_env)
        shprint(cmd, "-i", "", "/^speedups = Feature/,/^)$/s/.*//g", "./setup.py", _env=build_env)
        shprint(cmd, "-i", "", "s/features\['speedups'\].*=.*speedups/pass/g", "./setup.py", _env=build_env)  # noqa: W605
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = MarkupSafeRecipe()
