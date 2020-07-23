from kivy_ios.toolchain import Recipe, shprint, cd, cache_execution
import sh
from os.path import join


class HostSetuptools3(Recipe):
    depends = ["openssl", "hostpython3", "python3"]
    archs = ["x86_64"]
    version = '49.2.0'
    url = 'https://pypi.python.org/packages/source/s/setuptools/setuptools-{version}.zip'

    @cache_execution
    def install(self):
        arch = self.filtered_archs[0]
        build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)
        with cd(build_dir):
            shprint(hostpython, "setup.py", "install")

            # Copy in pkg_resources folder as it's otherwise not found
            sh.cp("-R", "pkg_resources/",
                  join(self.ctx.site_packages_dir, "pkg_resources"))
            sh.touch(join(self.ctx.site_packages_dir, "pkg_resources",
                     "py31compat.py"))

recipe = HostSetuptools3()
