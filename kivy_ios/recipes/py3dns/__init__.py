from kivy_ios.toolchain import PythonRecipe


class Py3DNSRecipe(PythonRecipe):
    site_packages_name = 'DNS'
    version = '3.2.1'
    url = 'https://launchpad.net/py3dns/trunk/{version}/' \
          '+download/py3dns-{version}.tar.gz'
    depends = ['host_setuptools3']

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return

        self.apply_patch("ios.patch")
        self.set_marker("patched")


recipe = Py3DNSRecipe()
