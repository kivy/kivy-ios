from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import shutil


class FreetypeRecipe(Recipe):
    version = "2.5.5"
    url = "http://download.savannah.gnu.org/releases/freetype/freetype-{version}.tar.bz2"
    library = "objs/.libs/libfreetype.a"
    include_dir = "include"

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


recipe = FreetypeRecipe()

