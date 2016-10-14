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
        #dest_dir = join(self.ctx.dist_dir, "root", "python")
        #build_env = arch.get_env()
        #build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        # shprint(hostpython, "./ez_setup.py", "--to-dir", dest_dir)
        #shprint(hostpython, "./ez_setup.py", _env=build_env)
        shprint(hostpython, "./ez_setup.py")

recipe = HostSetuptools()
