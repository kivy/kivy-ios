from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class LbryumRecipe(PythonRecipe):
    version = "v3.2.2rc1"
    url = "https://github.com/lbryio/lbryum/archive/{version}.tar.gz"
    depends = ["python", "setuptools", "appdirs", "ecdsa", "jsonrpclib", "keyring", "lbryschema"]
    
    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = arch.get_env()
        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(hostpython, "setup.py", "install", "--prefix", dest_dir, _env=build_env)

recipe = LbryumRecipe()
