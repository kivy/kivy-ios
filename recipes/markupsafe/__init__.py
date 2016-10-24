# pure-python package, this can be removed when we'll support any python package
from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class MarkupSafeRecipe(PythonRecipe):
    version = "master"
    url = "https://github.com/mitsuhiko/markupsafe/archive/{version}.zip"
    depends = ["python"]

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        cmd = sh.Command("sed")
        shprint(cmd, "-i", "", "s/,.*Feature//g", "./setup.py", _env=build_env)
        shprint(cmd, "-i", "", "s/setuptools/distutils.core/g", "./setup.py", _env=build_env)
        shprint(cmd, "-i", "", "/^speedups = Feature/,/^)$/s/.*//g", "./setup.py", _env=build_env)
        shprint(cmd, "-i", "", "s/features\['speedups'\].*=.*speedups/pass/g", "./setup.py", _env=build_env)
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = MarkupSafeRecipe()

