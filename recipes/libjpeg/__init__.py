from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class JpegRecipe(Recipe):
    version = "v9a"
    url = "http://www.ijg.org/files/jpegsrc.{}.tar.gz".format(version)
    library = "libjpeg.la"
    include_dir = [
        ("jpeglib.h", ""),
        ("cdjpeg.h", ""),
        ("jconfig.h", ""),
        ("jdct.h", ""),
        ("jerror.h", ""),
        ("jinclude.h", ""),
        ("jmemsys.h", ""),
        ("jmorecfg.h", ""),
        ("jpegint.h", ""),
        ("jversion.h", ""),
        ("transupp.h", "")
        ]
    include_per_arch = True


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
                "--enable-static=yes",
                "--enable-shared=no")
        shprint(sh.make, "clean")
        shprint(sh.make)

recipe = JpegRecipe()


