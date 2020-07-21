from kivy_ios.toolchain import Recipe
from os.path import join
import sh


class pkg_resources(Recipe):
    depends = ["hostpython", "python"]
    archs = ["x86_64"]
    url = ""

    def prebuild_arch(self, arch):
        sh.cp("-R", "pkg_resources/",
              join(self.ctx.site_packages_dir, "pkg_resources"))


recipe = pkg_resources()
