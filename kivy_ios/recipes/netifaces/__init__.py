import sh

from os.path import join

from kivy_ios.toolchain import CythonRecipe, cd, shprint


class NetifacesRecipe(CythonRecipe):
    """
    Also requires `setuptools to be installed on target (for pkg_resources):
    ```sh
    python toolchain.py pip install setuptools
    ```
    """

    version = "0.10.9"
    url = "https://pypi.io/packages/source/n/netifaces/netifaces-{version}.tar.gz"
    depends = ["python3", "host_setuptools3"]
    library = "libnetifaces.a"
    cythonize = False

    def dest_dir(self):
        return join(self.ctx.dist_dir, "root", "python3")

    def get_netifaces_env(self, arch):
        build_env = arch.get_env()
        build_env["PYTHONPATH"] = join(
            self.dest_dir(), "lib", "python3.8", "site-packages"
        )
        return build_env

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        build_env = self.get_netifaces_env(arch)
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
