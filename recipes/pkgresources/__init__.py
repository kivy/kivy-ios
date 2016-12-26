from toolchain import Recipe, shprint
from os.path import join
import sh
import os


class pkg_resources(Recipe):
    depends = ["hostpython", "python"]
    archs = ['i386']
    url = "pkgr"

    def prebuild_arch(self, arch):
        pkgdir = join(self.ctx.dist_dir, "root", "python", "lib", "python2.7", "site-packages", "pkg_resources")
        if not os.path.exists(pkgdir):
            sh.mkdir(pkgdir)
        sh.cp("-a", "./", pkgdir)
        #sh.pip('install', '-t', join(self.ctx.dist_dir, "root", "python", "lib", "python2.7", "site-packages"))


recipe = pkg_resources()


