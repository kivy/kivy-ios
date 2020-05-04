from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh
import logging

logger = logging.getLogger(__name__)


class HostOpensslRecipe(Recipe):
    version = "1.1.1f"
    url = "http://www.openssl.org/source/openssl-{version}.tar.gz"
    archs = ["x86_64"]

    def get_build_env(self):
        build_env = self.ctx.env.copy()
        self.build_env_x86_84 = build_env
        return build_env

    def build_x86_64(self):
        build_env = self.get_build_env()
        configure = sh.Command(join(self.build_dir, "Configure"))
        shprint(configure,
                "darwin64-x86_64-cc",
                _env=build_env)
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, "build_libs")

    def install(self):
        sh.mkdir('-p', join(self.ctx.dist_dir, 'hostopenssl'))
        sh.cp('-r', join(self.get_build_dir('x86_64'), 'include'),
              join(self.ctx.dist_dir, 'hostopenssl', 'include'))
        sh.mkdir('-p', join(self.ctx.dist_dir, 'hostopenssl', 'lib'))
        sh.cp(join(self.get_build_dir('x86_64'), 'libssl.a'),
              join(self.ctx.dist_dir, 'hostopenssl', 'lib'))
        sh.cp(join(self.get_build_dir('x86_64'), 'libcrypto.a'),
              join(self.ctx.dist_dir, 'hostopenssl', 'lib'))


recipe = HostOpensslRecipe()
