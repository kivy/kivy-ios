from toolchain import CythonRecipe


class SetuptoolsRecipe(CythonRecipe):
    name = "setuptools"
    version = "4.3.2"
    url = 'https://pypi.python.org/packages/f1/92/12c7251039b274c30106c3e0babdcb040cbd13c3ad4b3f0ef9a7c217e36a/setuptools-30.2.0.tar.gz'
    depends = ["python", "host_setuptools"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(SetuptoolsRecipe, self).get_recipe_env(arch)
        env["PYTHONPATH"] = self.get_build_dir(arch.arch) + "/iosbuild/lib/python2.7/site-packages"
        return env

    def install_python_package(self):
        import sh
        from toolchain import shprint
        from os import chdir
        arch = self.filtered_archs[0]
        build_dir = self.get_build_dir(arch.arch)
        chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        shprint(hostpython, "setup.py", "install", "--prefix",
        self.ctx.install_dir, "--old-and-unmanageable")
        # "--single-version-externally-managed", "--root", "/", "-O2")




recipe = SetuptoolsRecipe()

