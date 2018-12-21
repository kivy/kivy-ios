from toolchain import Recipe,shprint
from multiprocessing import cpu_count
from os.path import join
import sh

class LibIconvRecipe(Recipe):
    print('Debug')
    version = "1.15"
    url = 'https://ftp.gnu.org/pub/gnu/libiconv/libiconv-{version}.tar.gz'
    library = "lib/.libs/libiconv.a"

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
                '--target={}'.format(arch.triple),
                "--disable-shared")
        shprint(sh.make, "clean")
        shprint(sh.make, _env=build_env)


recipe = LibIconvRecipe()


