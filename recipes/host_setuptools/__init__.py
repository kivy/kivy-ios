from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class HostSetuptools(Recipe):
    depends = ["openssl", "hostpython"]
    archs = ["x86_64"]
    url = "setuptools"

    def get_stt_env(self, arch):
        build_env = arch.get_env()
        build_env["IOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["ARCH"] = arch.arch
        build_env["C_INCLUDE_PATH"] = join(arch.sysroot, "usr", "include")
        build_env["LIBRARY_PATH"] = join(arch.sysroot, "usr", "lib")
        build_env["CFLAGS"] = " ".join([
            "-I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "freetype")) +
            " -I{}".format(join(self.ctx.dist_dir, "include", arch.arch, "libjpeg")) +
            " -arch {}".format(arch.arch)
            ])
        return build_env


    def prebuild_arch(self, arch):
        hostpython = sh.Command(self.ctx.hostpython)
        sh.curl("-O",  "https://bootstrap.pypa.io/ez_setup.py")
        shprint(hostpython, "./ez_setup.py", _env=self.get_stt_env(arch))
        # Extract setuptools egg and remove .pth files. Otherwise subsequent
        # python package installations using setuptools will raise exceptions.
        # Setuptools version 28.3.0
        site_packages_path = join(
            self.ctx.dist_dir, 'hostpython',
            'lib', 'python2.7', 'site-packages')
        os.chdir(site_packages_path)
        with open('setuptools.pth', 'r') as f:
            setuptools_egg_path = f.read().strip('./').strip('\n')
            unzip = sh.Command('unzip')
            shprint(unzip, setuptools_egg_path)
        #os.remove(setuptools_egg_path)
        #os.remove('setuptools.pth')
        #os.remove('easy-install.pth')
        #shutil.rmtree('EGG-INFO')

recipe = HostSetuptools()
