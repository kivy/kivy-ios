from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class CurlRecipe(Recipe):
    version = "7.65.3"
    url = "https://curl.haxx.se/download/curl-{version}.tar.gz"
    library = "lib/.libs/libcurl.a"
    include_dir = "include"
    depends = ["openssl"]

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
                "--disable-shared",
                "--without-libidn2")
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make)


recipe = CurlRecipe()
