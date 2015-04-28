from toolchain import Recipe, shprint
from os.path import join
import sh


class FFMpegRecipe(Recipe):
    version = "2.5.4"
    url = "http://www.ffmpeg.org/releases/ffmpeg-{version}.tar.bz2"
    include_per_arch = True
    include_dir = "dist/include"
    libraries = [
        "libavcodec/libavcodec.a",
        "libavdevice/libavdevice.a",
        "libavfilter/libavfilter.a",
        "libavformat/libavformat.a",
        "libavresample/libavresample.a",
        "libavutil/libavutil.a",
        "libswresample/libswresample.a",
        "libswscale/libswscale.a"]

    def build_arch(self, arch):
        options = (
            "--enable-cross-compile",
            "--disable-debug",
            "--disable-programs",
            "--disable-doc",
            "--enable-pic",
            "--enable-avresample")
        build_env = arch.get_env()
        build_env["VERBOSE"] = "1"
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "--target-os=darwin",
                "--arch={}".format(arch.arch),
                "--cc={}".format(build_env["CC"]),
                "--prefix={}/dist".format(self.build_dir),
                "--extra-cflags={}".format(build_env["CFLAGS"]),
                "--extra-cxxflags={}".format(build_env["CFLAGS"]),
                "--extra-ldflags={}".format(build_env["LDFLAGS"]),
                *options,
                _env=build_env)
        shprint(sh.make, "clean", _env=build_env)
        shprint(sh.make, "-j3", _env=build_env)
        shprint(sh.make, "install")


recipe = FFMpegRecipe()

