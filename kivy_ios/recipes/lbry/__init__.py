from kivy_ios.toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class LbryRecipe(PythonRecipe):
    version = "v0.81.0"
    url = "https://github.com/lbryio/lbry/archive/{version}.tar.gz"
    depends = [
        "python",
        "setuptools",
        "aiohttp",
        "aioupnp",
        "appdirs",
        "argparse",
        "async_timeout",
        "base58",
        "chardet",
        "coincurve",
        "colorama",
        "cryptography",
        "defusedxml"
        "docopt",
        "ecdsa",
        "hachoir",
        "keyring",
        "mock",
        "msgpack",
        "pbkdf2",
        "prometheus_client"
        "pylru",
        "pyyaml",
        "six",
    ]
    
    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.8', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = LbryRecipe()
