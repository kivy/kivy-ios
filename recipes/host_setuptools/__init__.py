from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class HostSetuptools(Recipe):
    depends = ["openssl", "hostpython"]
    archs = ["x86_64"]
    #url = "setuptools"
    version = "18.5"
    url = "https://pypi.python.org/packages/source/s/setuptools/setuptools-{version}.tar.gz"
    cythonize = False

    '''
    def prebuild_arch(self, arch):
        dest_dir = join(
            self.ctx.dist_dir, 'hostpython',
            'lib', 'python2.7', 'site-packages')
        #hostpython = sh.Command(self.ctx.hostpython)
        #sh.curl("-O",  "https://bootstrap.pypa.io/ez_setup.py")
        #shprint(hostpython, "./ez_setup.py")
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
        os.remove(setuptools_egg_path)
        os.remove('setuptools.pth')
        os.remove('easy-install.pth')
        shutil.rmtree('EGG-INFO')
    '''
    
    def install(self):
        import sh
        from toolchain import shprint
        from os import chdir
        arch = self.filtered_archs[0]
        build_dir = self.get_build_dir(arch.arch)
        chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        shprint(hostpython, "setup.py", "install", "--prefix", "{}/hostpython".format(self.ctx.dist_dir))
    
recipe = HostSetuptools()
