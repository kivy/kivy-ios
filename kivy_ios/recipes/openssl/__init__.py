from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


arch_mapper = {'x86_64': 'darwin64-x86_64-cc',
               'arm64': 'ios64-cross'}


class OpensslRecipe(Recipe):
    version = "1.1.1l"
    url = "http://www.openssl.org/source/openssl-{version}.tar.gz"
    libraries = ["libssl.a", "libcrypto.a"]
    include_dir = "include"
    include_per_arch = True

    def build_arch(self, arch):
        build_env = arch.get_env()
        target = arch_mapper[arch.arch]
        shprint(sh.env, _env=build_env)
        sh.perl(join(self.build_dir, "Configure"),
                target,
                _env=build_env)
        if target.endswith('-cross'):
            with open('Makefile', 'r') as makefile:
                filedata = makefile.read()
            filedata = filedata.replace('$(CROSS_TOP)/SDKs/$(CROSS_SDK)', arch.sysroot)
            with open('Makefile', 'w') as makefile:
                makefile.write(filedata)
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, "build_libs")


recipe = OpensslRecipe()
