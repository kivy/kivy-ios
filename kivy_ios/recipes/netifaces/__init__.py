import sh

from os.path import join

from kivy_ios.toolchain import CythonRecipe, shprint
from kivy_ios.context_managers import cd


class NetifacesRecipe(CythonRecipe):
    version = "0.10.9"
    url = "https://pypi.io/packages/source/n/netifaces/netifaces-{version}.tar.gz"
    depends = ["python3"]
    python_depends = ["setuptools"]
    hostpython_prerequisites = ["Cython==0.29.37"]
    library = "libnetifaces.a"
    cythonize = False

    def dest_dir(self):
        return join(self.ctx.dist_dir, "root", "python3")

    def get_netifaces_env(self, plat):
        build_env = plat.get_env()
        build_env["PYTHONPATH"] = self.ctx.site_packages_dir
        return build_env

    def install(self):
        plat = list(self.platforms_to_build)[0]
        build_dir = self.get_build_dir(plat)
        build_env = self.get_netifaces_env(plat)
        hostpython = sh.Command(self.ctx.hostpython)
        with cd(build_dir):
            shprint(
                hostpython,
                "setup.py",
                "install",
                "--prefix",
                self.dest_dir(),
                _env=build_env,
            )


recipe = NetifacesRecipe()
