from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class LbryRecipe(PythonRecipe):
    version = "v0.20.0rc10"
    url = "https://github.com/lbryio/lbry/archive/{version}.tar.gz"
    depends = [
        "python",
        "setuptools",
        "twisted",
        "cryptography",
        "appdirs",
        "argparse",
        "docopt",
        "base58",
        "colorama",
        "dnspython",
        "ecdsa",
        "envparse",
        "jsonrpc",
        "jsonrpclib",
        "keyring",
        "lbryschema",
        "lbryum",
        "miniupnpc",
        "pbkdf2",
        "pyyaml",
        "pygithub",
        "qrcode",
        "requests",
        "service_identity",
        "six",
        "slowaes",
        "txjson-rpc",
        "wsgiref",
        "zope_interface",
        "treq"
    ]
    
    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = LbryRecipe()
