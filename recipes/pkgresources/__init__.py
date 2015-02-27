from toolchain import Recipe, shprint
from os.path import join
import sh
import os


class pkg_resources(Recipe):
    depends = ["hostpython", "python"]
    archs = ['i386']
    url = ""

    def prebuild_arch(self, arch):
        sh.cp("pkg_resources.py", join(self.ctx.dist_dir, "root", "python", "lib", "python2.7", "site-packages", "pkg_resources.py"))

recipe = pkg_resources()


