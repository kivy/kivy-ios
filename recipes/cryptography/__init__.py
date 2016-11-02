from os.path import join
from toolchain import CythonRecipe
from toolchain import shprint
import sh


class CryptographyRecipe(CythonRecipe):
    name = "cryptography"
    version = "1.5.2"
    url = (
        "https://pypi.python.org/packages/03/1a/"
        "60984cb85cc38c4ebdfca27b32a6df6f1914959d8790f5a349608c78be61/"
        "cryptography-{version}.tar.gz"
    )
    depends = ["host_setuptools", "cffi", "six", "idna", "pyasn1", "enum34"]
    cythonize = False

    def get_recipe_env(self, arch):
        #env['LN_FLAGS'] = "-lboost_thread-mt"
        #env['PKG_CONFIG_PATH'] = join(self.ctx.dist_dir, "include", arch.arch, "libffi")
        #env['PKG_CONFIG_PATH'] += ":" + join(self.ctx.dist_dir, "include", arch.arch, "openssl")
        """
        libffi_include = dict()
        libffi_include['arm64'] = 'build_iphoneos-arm64'
        libffi_include['armv7'] = 'build_iphoneos-armv7'
        libffi_include['i386'] = 'build_iphonesimulator-i386'
        libffi_include['x86_64'] = 'build_iphonesimulator-x86_64'
        include_path = join(
            self.ctx.build_dir, 'libffi', arch.arch,
            'libffi-3.2.1', libffi_include[arch.arch])
        env['PKG_CONFIG_PATH'] = include_path
        env["CC"] += " -I{}".format(include_path)
        env["CC"] += " -I{}".format(
                            join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        # env["CFLAGS"]
        #env["CFLAGS"] += " -I{}".format(
        #    join(self.ctx.dist_dir, "include", arch.arch, "openssl", "openssl"))
        """
        #dest_dir = join(self.ctx.dist_dir, "root", "python")
        #pythonpath = join(dest_dir, "lib", "python2.7", "site-packages")
        #env["PYTHONPATH"] = pythonpath
        #env["CC"] += " -I{}".format(
        #    join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        #env["LDFLAGS"] += "-L{}".format(
        #    join(self.ctx.dist_dir, "hostlibffi", "usr", "local", "lib"))
        #env["CFLAGS"] += "-I{}".format(
        #    join(self.ctx.dist_dir, "hostlibffi", "usr", "local", "include"))
        env = super(CryptographyRecipe, self).get_recipe_env(arch)
        r = self.get_recipe('openssl', self.ctx)
        openssl_dir = r.get_build_dir(arch.arch)
        env['PYTHON_ROOT'] = join(self.ctx.dist_dir, 'root', 'python')
        env['CFLAGS'] += ' -I' + env['PYTHON_ROOT'] + '/include/python2.7' + \
                         ' -I' + join(openssl_dir, 'include')
        # Set linker to use the correct gcc
        env['LDSHARED'] = env['CC'] + ' -pthread -shared -Wl,-O1 -Wl,-Bsymbolic-functions'
        env['LDFLAGS'] += ' -L' + env['PYTHON_ROOT'] + '/lib' + \
                          ' -L' + openssl_dir + \
                          ' -lpython2.7' + \
                          ' -lssl' + r.version + \
                          ' -lcrypto' + r.version
        return env

recipe = CryptographyRecipe()

