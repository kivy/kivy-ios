'''Recipe for pycrypto on ios
'''
from toolchain import CythonRecipe, shprint
from os.path import join, exists
import sh
import os


class PycryptoRecipe(CythonRecipe):
    version = "2.6.1"
    url = "https://ftp.dlitz.net/pub/dlitz/crypto/pycrypto/pycrypto-{version}.tar.gz"
    #url = 'src'
    depends = ["python", "openssl"]
    #cythonize = False
    include_per_arch = True
    library="libpycrypto.a"
    #pre_build_ext = True


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
                "ac_cv_func_realloc_0_nonnull=yes",
                #"enable-static=yes",
                #"enable-shared=no"
               )     
        hostpython = sh.Command(self.ctx.hostpython)
        #shprint(hostpython, "setup.py", "build_ext", "--inplace", "-v",
        #        _env=build_env)
        super(PycryptoRecipe, self).build_arch(arch)

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "-m", "easy_install",
                "--prefix", dest_dir, "-Z", "./",
                _env=build_env)
        #print('installing to {}').format(dest_dir)
        #shprint(hostpython, "setup.py", "install", "--home={}".format(dest_dir + '/lib/python2.7'), _env=build_env)
        #shprint(hostpython, "-m", "pip", "install", "--root", dest_dir, "./")

recipe = PycryptoRecipe()
