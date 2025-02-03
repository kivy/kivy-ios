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
    include_per_platform = True
    library = "libpycrypto.a"
    hostpython_prerequisites = ["Cython==0.29.37"]

    def build_platform(self, plat):
        build_env = plat.get_env()
        self.apply_patch('hash_SHA2_template.c.patch', target_dir=self.build_dir + '/src')
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure,
                "CC={}".format(build_env["CC"]),
                "LD={}".format(build_env["LD"]),
                "CFLAGS={}".format(build_env["CFLAGS"]),
                "LDFLAGS={} -Wno-error ".format(build_env["LDFLAGS"]),
                "--prefix=/",
                "--host={}".format(plat),
                "ac_cv_func_malloc_0_nonnull=yes",
                "ac_cv_func_realloc_0_nonnull=yes")
        super(PycryptoRecipe, self).build_platform(plat)

    def install(self):
        plat = list(self.platforms_to_build)[0]
        build_dir = self.get_build_dir(plat)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = plat.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.7', 'site-packages')
        with cd(build_dir):
            shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)


recipe = PycryptoRecipe()
