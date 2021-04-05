from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class JpegRecipe(Recipe):
    version = "v9d"
    url = "http://www.ijg.org/files/jpegsrc.{version}.tar.gz"
    library = ".libs/libjpeg.a"
    include_dir = [
        ("jpeglib.h", ""),
        ("jconfig.h", ""),
        ("jerror.h", ""),
        ("jmorecfg.h", ""),
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
                "--disable-shared")
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make)


recipe = JpegRecipe()
