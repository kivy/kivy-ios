from kivy_ios.toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class LbryRecipe(PythonRecipe):
    version = "f7eed62"
    url = "https://github.com/lbryio/lbry/archive/{version}.tar.gz"
    depends = [
        "python",
        "ios",
        "pyobjus",
        "kivy",
        
        # install_requires dependencies
        "aiohttp",
        "aioupnp",
        "appdirs",
        "async-timeout",
        "base58",
        "chardet",
        "coincurve",
        "colorama",
        "cryptography",
        "defusedxml",
        "docopt",
        "ecdsa",
        "hachoir",
        "keyring",
        "mock",
        "msgpack",
        "pbkdf2",
        "prometheus_client",
        "protobuf",
        "pylru",
        "pyyaml",
        "six"
    ]
    
    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("setup_override.patch")
        self.set_marker("patched")
    
    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python3")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.8', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = LbryRecipe()
