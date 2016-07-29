from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class HostSetuptools(Recipe):
    depends = ["hostpython"]
    archs = ["x86_64"]
    url = ""

    def prebuild_arch(self, arch):
        hostpython = sh.Command(self.ctx.hostpython)
        sh.curl("-O",  "https://bootstrap.pypa.io/ez_setup.py")
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env = arch.get_env()
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        # shprint(hostpython, "./ez_setup.py", "--to-dir", dest_dir)
        shprint(hostpython, "./ez_setup.py", _env=build_env)

    # def install(self):
    #     arch = list(self.filtered_archs)[0]
    #     build_dir = self.get_build_dir(arch.arch)
    #     os.chdir(build_dir)
    #     hostpython = sh.Command(self.ctx.hostpython)
    #     build_env = arch.get_env()
    #     dest_dir = join(self.ctx.dist_dir, "root", "python")
    #     build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
    #     shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = HostSetuptools()
