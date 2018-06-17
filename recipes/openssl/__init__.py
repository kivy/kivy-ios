from toolchain import Recipe, shprint
from os.path import join
import sh


arch_mapper = {'i386': 'darwin-i386-cc',
               'x86_64': 'darwin64-x86_64-cc',
               'armv7': 'iphoneos-cross',
               'arm64': 'iphoneos-cross'}


class OpensslRecipe(Recipe):
    version = "1.0.2k"
    url = "http://www.openssl.org/source/openssl-{version}.tar.gz"
    libraries = ["libssl.a", "libcrypto.a"]
    include_dir = "include"
    include_per_arch = True

    def build_arch(self, arch):
        options_iphoneos = (
            "-isysroot {}".format(arch.sysroot),
            "-DOPENSSL_THREADS",
            "-D_REENTRANT",
            "-DDSO_DLFCN",
            "-DHAVE_DLFCN_H",
            "-fomit-frame-pointer",
            "-fno-common",
            "-O3"
        )
        build_env = arch.get_env()
        target = arch_mapper[arch.arch]
        shprint(sh.env, _env=build_env)
        sh.perl(join(self.build_dir, "Configure"),
                target,
                _env=build_env)
        if target == 'iphoneos-cross':
            sh.sed("-ie", "s!^CFLAG=.*!CFLAG={} {}!".format(build_env['CFLAGS'],
                   " ".join(options_iphoneos)),
                   "Makefile")
            sh.sed("-ie", "s!static volatile sig_atomic_t intr_signal;!static volatile intr_signal;! ",
                   "crypto/ui/ui_openssl.c")
        else:
            sh.sed("-ie", "s!^CFLAG=!CFLAG={} !".format(build_env['CFLAGS']),
                   "Makefile")
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, "build_libs")

recipe = OpensslRecipe()
