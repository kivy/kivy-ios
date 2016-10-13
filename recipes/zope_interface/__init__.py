from toolchain import PythonRecipe, shprint
from os.path import join
import sh, os

class ZopeInterfaceRecipe(PythonRecipe):
    version = "4.3.2"
    url="https://github.com/zopefoundation/zope.interface/archive/{version}.zip"
    depends = ["python", "hostsetuptools"]
    include_per_arch = True

    def get_environ(self, arch):
        build_env = arch.get_env()
        build_env["IOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["ARCH"] = arch.arch
        return build_env

    def build_arch(self, arch):
        print '########### build arch: ' + arch.arch
        build_env = self.get_environ(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        shprint(hostpython, "setup.py", "build_ext", _env=build_env)

    def install(self):
        arch = list(self.filtered_archs)[0]
        print '########### install arch: ' + arch.arch
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = self.get_environ(arch)
        dest_dir = os.path.join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = os.path.join(
            dest_dir, 'lib', 'python2.7', 'site-packages')
        shprint(
            hostpython, "setup.py", "install", "--prefix", dest_dir,
            _env=build_env)

recipe = ZopeInterfaceRecipe()
