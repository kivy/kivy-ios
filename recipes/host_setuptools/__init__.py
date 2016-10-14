from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class HostSetuptools(Recipe):
    depends = ["hostpython"]
    archs = ["x86_64"]
    url = "setuptools"

    def prebuild_arch(self, arch):
        hostpython = sh.Command(self.ctx.hostpython)
        sh.curl("-O",  "https://bootstrap.pypa.io/ez_setup.py")
        shprint(hostpython, "./ez_setup.py")

recipe = HostSetuptools()
