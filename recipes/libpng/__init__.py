# -*- coding: utf-8 -*-
from toolchain import Recipe, shprint
from os.path import join
import sh

class PngRecipe(Recipe):
    version = '1.6.24'
    url = 'http://vorboss.dl.sourceforge.net/project/libpng/libpng16/1.6.24/libpng-1.6.24.tar.gz'
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
        shprint(sh.make, _env=build_env)

recipe = PngRecipe()