from kivy_ios.toolchain import HostRecipe, shprint, cache_execution
from kivy_ios.context_managers import cd, python_path
import sh


class HostSetuptools3(HostRecipe):
    depends = ["openssl", "hostpython3", "python3"]
    version = '67.3.2'
    url = 'https://pypi.python.org/packages/source/s/setuptools/setuptools-{version}.tar.gz'

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("allow-cflags-override.patch")
        self.set_marker("patched")

    @cache_execution
    def install(self):
        arch = self.filtered_archs[0]
        build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)

        with python_path(self.ctx.site_packages_dir):
            with cd(build_dir):
                shprint(hostpython, "setup.py", "install",
                        f"--prefix={self.ctx.python_prefix}")


recipe = HostSetuptools3()
