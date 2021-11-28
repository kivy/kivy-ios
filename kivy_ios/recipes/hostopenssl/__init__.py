from kivy_ios.toolchain import HostRecipe, shprint
from os.path import join
import sh
import logging

logger = logging.getLogger(__name__)

arch_mapper = {'x86_64': 'darwin64-x86_64-cc',
               'arm64': 'darwin64-arm64-cc'}


class HostOpensslRecipe(HostRecipe):
    version = "1.1.1l"
    url = "http://www.openssl.org/source/openssl-{version}.tar.gz"

    def get_build_env(self):
        build_env = self.ctx.env.copy()
        self.build_env = build_env
        return build_env

    def build_arch(self, arch):
        build_env = self.get_build_env()
        configure = sh.Command(join(self.build_dir, "Configure"))
        shprint(configure,
                arch_mapper[arch.arch],
                _env=build_env)
        shprint(sh.make, "clean")
        shprint(sh.make, self.ctx.concurrent_make, "build_libs")

    def install(self):
        arch = self.archs[0]
        sh.mkdir('-p', join(self.ctx.dist_dir, 'hostopenssl'))
        sh.cp('-r', join(self.get_build_dir(arch), 'include'),
              join(self.ctx.dist_dir, 'hostopenssl', 'include'))
        sh.mkdir('-p', join(self.ctx.dist_dir, 'hostopenssl', 'lib'))
        sh.cp(join(self.get_build_dir(arch), 'libssl.a'),
              join(self.ctx.dist_dir, 'hostopenssl', 'lib'))
        sh.cp(join(self.get_build_dir(arch), 'libcrypto.a'),
              join(self.ctx.dist_dir, 'hostopenssl', 'lib'))


recipe = HostOpensslRecipe()
