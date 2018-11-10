from toolchain import Recipe, shprint
from os.path import join
import sh


class pkg_resources(Recipe):
    depends = ["hostpython", "python"]
    archs = ["x86_64"]
    url = ""

    def prebuild_arch(self, arch):
        sh.cp("pkg_resources.py",
            join(self.ctx.site_packages_dir, "pkg_resources.py"))


recipe = pkg_resources()
