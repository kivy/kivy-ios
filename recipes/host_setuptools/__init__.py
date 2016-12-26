import sh

from toolchain import Recipe, shprint


class HostSetuptools(Recipe):
    depends = ["openssl", "hostpython"]
    archs = ["x86_64"]
    url = "setuptools"

    def prebuild_arch(self, arch):
        hostpython = sh.Command(self.ctx.hostpython)
        sh.curl("-O",  "https://bootstrap.pypa.io/ez_setup.py")
        shprint(hostpython, "./ez_setup.py")

recipe = HostSetuptools()
