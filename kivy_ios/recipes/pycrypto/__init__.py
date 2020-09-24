'''Recipe for pycrypto on ios
'''
from kivy_ios.toolchain import CythonRecipe, shprint
from kivy_ios.context_managers import cd
from os.path import join
import sh


class PycryptoRecipe(CythonRecipe):
    version = "2.6.1"
    url = "https://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-{version}.tar.gz"
    depends = ["python", "openssl"]
    include_per_arch = True
    library = "libpycrypto.a"

    def build_arch(self, arch):
        build_env = arch.get_env()
        self.apply_patch('hash_SHA2_template.c.patch', target_dir=self.build_dir + '/src')
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={} -Wno-error ".format(build_env["LDFLAGS"]),
                "--prefix=/",
                "--host={}".format(arch),
                "ac_cv_func_malloc_0_nonnull=yes",
                "ac_cv_func_realloc_0_nonnull=yes")
        super(PycryptoRecipe, self).build_arch(arch)

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.7', 'site-packages')
        with cd(build_dir):
            shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = PycryptoRecipe()
