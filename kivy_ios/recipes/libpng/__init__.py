# -*- coding: utf-8 -*-
from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class PngRecipe(Recipe):
    version = '1.6.40'
    url = 'https://downloads.sourceforge.net/sourceforge/libpng/libpng-{version}.tar.gz'
    library = 'dist/lib/libpng16.a'
    include_dir = 'dist/include'

    def build_platform(self, plat):
        build_env = plat.get_env()
        configure = sh.Command(join(self.build_dir, "configure"))

        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={}".format(build_env["LDFLAGS"]),
                "--prefix={}".format(join(self.build_dir, "dist")),
                "--host={}".format(plat.triple),
                "--disable-shared")
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, _env=build_env)
        shprint(sh.make, "install", _env=build_env)


recipe = PngRecipe()
