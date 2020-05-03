# -*- coding: utf-8 -*-
from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class PngRecipe(Recipe):
    version = '1.6.26'
    url = 'http://downloads.sourceforge.net/sourceforge/libpng/libpng-{version}.tar.gz'
    depends = ["python"]
    library = '.libs/libpng16.a'

    def build_arch(self, arch):
        build_env = arch.get_env()
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={}".format(build_env["LDFLAGS"]),
                "--prefix=/",
                "--host={}".format(arch.triple),
                "--disable-shared")
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, _env=build_env)


recipe = PngRecipe()
