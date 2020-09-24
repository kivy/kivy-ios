from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh
import os
import shutil


class HostSetuptools(Recipe):
    depends = ["openssl", "hostpython"]
    archs = ["x86_64"]
    url = "setuptools"

    def prebuild_arch(self, arch):
        hostpython = sh.Command(self.ctx.hostpython)
        sh.curl("-O", "https://bootstrap.pypa.io/ez_setup.py")
        shprint(hostpython, "./ez_setup.py")
        # Extract setuptools egg and remove .pth files. Otherwise subsequent
        # python package installations using setuptools will raise exceptions.
        # Setuptools version 28.3.0
        site_packages_path = join(
            self.ctx.dist_dir, 'hostpython',
            'lib', 'python3.7', 'site-packages')
        os.chdir(site_packages_path)
        with open('setuptools.pth', 'r') as f:
            setuptools_egg_path = f.read().strip('./').strip('\n')
            unzip = sh.Command('unzip')
            shprint(unzip, setuptools_egg_path)
        os.remove(setuptools_egg_path)
        os.remove('setuptools.pth')
        os.remove('easy-install.pth')
        shutil.rmtree('EGG-INFO')


recipe = HostSetuptools()
