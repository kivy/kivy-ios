from kivy_ios.toolchain import CythonRecipe


class SetuptoolsRecipe(CythonRecipe):
    name = "setuptools"
    version = "18.5"
    url = "https://pypi.python.org/packages/source/s/setuptools/setuptools-{version}.tar.gz"
    depends = ["python", "host_setuptools"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(SetuptoolsRecipe, self).get_recipe_env(arch)
        env["PYTHONPATH"] = self.get_build_dir(arch.arch) + "/iosbuild/lib/python3.8/site-packages"
        return env

    def install(self):
        import sh
        from toolchain import shprint
        from os import chdir
        arch = self.filtered_archs[0]
        
        build_env = arch.get_env()
        
        build_dir = self.get_build_dir(arch.arch)
        chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        shprint(hostpython, "setup.py", "install", "--prefix", self.ctx.install_dir, "--old-and-unmanageable")
        # "--single-version-externally-managed", "--root", "/", "-O2")


recipe = SetuptoolsRecipe()
