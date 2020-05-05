# pure-python package, this can be removed when we'll support any python package
from kivy_ios.toolchain import PythonRecipe, shprint, cd
from os.path import join
import sh


class ItsDangerousRecipe(PythonRecipe):
    version = "master"
    url = "https://github.com/mitsuhiko/itsdangerous/archive/{version}.zip"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.7', 'site-packages')
        cmd = sh.Command("sed")
        with cd(build_dir):
            shprint(cmd, "-i", "", "s/setuptools/distutils.core/g", "./setup.py", _env=build_env)
            shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = ItsDangerousRecipe()
