import os
import subprocess

from os.path import join

from toolchain import CythonRecipe


class NetifacesRecipe(CythonRecipe):
    version = '0.10.5'
    url = 'https://pypi.io/packages/source/n/netifaces/netifaces-{version}.tar.gz'
    depends = ['python', 'host_setuptools']
    library = "libnetifaces.a"

    def build_arch(self, arch):
        self.apply_patch('setup.patch')
        super(NetifacesRecipe, self).build_arch(arch)

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')

        env = ' '.join(['{}="{}"'.format(k, v) for k, v in build_env.iteritems()])
        cmd = ' '.join([env, self.ctx.hostpython, "-m", "easy_install", "--prefix", dest_dir, "-Z", "./"])
        out = subprocess.check_output(cmd, shell=True)
        print(out)


recipe = NetifacesRecipe()
