from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class CurlRecipe(Recipe):
    version = "7.88.1"
    url = "https://curl.haxx.se/download/curl-{version}.tar.gz"
    library = "lib/.libs/libcurl.a"
    include_dir = "include"
    depends = ["openssl"]

    def build_platform(self, plat):
        build_env = plat.get_env()
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={}".format(build_env["LDFLAGS"]),
                "PKG_CONFIG=ios-pkg-config",
                # ios-pkg-config does not exists,
                # is needed to disable the pkg-config usage.
                "--prefix=/",
                "--host={}".format(plat.triple),
                "--disable-shared",
                "--without-libidn2",
                "--with-openssl")
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make)


recipe = CurlRecipe()
