from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


plat_mapper = {
    'iphoneos-arm64': 'ios64-xcrun',
    'iphonesimulator-x86_64': 'iossimulator-xcrun',
    'iphonesimulator-arm64': 'iossimulator-xcrun',
}


class OpensslRecipe(Recipe):
    version = "1.1.1w"
    url = "http://www.openssl.org/source/openssl-{version}.tar.gz"
    libraries = ["libssl.a", "libcrypto.a"]
    include_dir = "include"
    include_per_platform = True

    def build_platform(self, plat):
        build_env = plat.get_env()
        target = plat_mapper[plat.name]
        shprint(sh.env, _env=build_env)
        sh.perl(join(self.build_dir, "Configure"), target, _env=build_env)
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, "build_libs")


recipe = OpensslRecipe()
