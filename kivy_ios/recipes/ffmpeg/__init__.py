from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class FFMpegRecipe(Recipe):
    version = "n4.3.1"
    url = "https://github.com/FFmpeg/FFmpeg/archive/{version}.zip"
    include_per_arch = True
    include_dir = "dist/include"
    optional_depends = ["openssl"]
    libraries = [
        "libavcodec/libavcodec.a",
        "libavdevice/libavdevice.a",
        "libavfilter/libavfilter.a",
        "libavformat/libavformat.a",
        "libavresample/libavresample.a",
        "libavutil/libavutil.a",
        "libswresample/libswresample.a",
        "libswscale/libswscale.a",
    ]
    pbx_frameworks = ["VideoToolbox"]

    def build_arch(self, arch):
        options = [
            "--disable-everything",
            "--enable-parsers",
            "--enable-decoders",
            "--enable-demuxers",
            "--enable-filter=aresample,resample,crop,scale",
            "--enable-protocol=file,http,rtmp",
            "--enable-pic",
            "--enable-small",
            "--enable-hwaccels",
            "--enable-static",
            "--disable-shared",
            # libpostproc is GPL: https://ffmpeg.org/pipermail/ffmpeg-user/2012-February/005162.html
            "--enable-gpl",
            # disable some unused algo
            # note: "golomb" are the one used in our video test, so don't use --disable-golomb
            # note: and for aac decoding: "rdft", "mdct", and "fft" are needed
            "--disable-dxva2",
            "--disable-vdpau",
            "--disable-vaapi",
            "--disable-dct",
            # disable binaries / doc
            "--enable-cross-compile",
            "--disable-debug",
            "--disable-programs",
            "--disable-doc",
            "--enable-pic",
            "--enable-avresample"]

        if "openssl.build_all" in self.ctx.state:
            options += [
                "--enable-openssl",
                "--enable-nonfree",
                "--enable-protocol=https,tls_openssl"]

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
                "--disable-x86asm",
                *options,
                _env=build_env)
        """
        shprint(sh.sed,
                "-i.bak",
                "s/HAVE_CLOSESOCKET=yes//g",
                "config.mak")
        shprint(sh.sed,
                "-i.bak",
                "s/#define HAVE_CLOSESOCKET 1//g",
                "config.h")
        if exists("config.asm"):
            shprint(sh.sed,
                    "-i.bak",
                    "s/%define HAVE_CLOSESOCKET 1//g",
                    "config.asm")
        """
        shprint(sh.make, "clean", _env=build_env)
        shprint(sh.make, self.ctx.concurrent_make, _env=build_env)
        shprint(sh.make, "install")


recipe = FFMpegRecipe()
