from toolchain import Recipe, shprint
from os.path import join
import sh

class HostpythonRecipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"

    def prebuild_arch(self, arch):
        # common to all archs
        if not self.has_marker("patched"):
            self.apply_patch("ssize-t-max.patch")
            self.apply_patch("dynload.patch")
            self.apply_patch("static-_sqlite3.patch")
            self.copy_file("ModulesSetup", "Modules/Setup.local")
            self.copy_file("_scproxy.py", "Lib/_scproxy.py")
            #self.copy_file("Setup.dist", "Modules/Setup.dist")
            self.set_marker("patched")
        super(HostpythonRecipe, self).prebuild_arch(arch)

    def build_i386(self):
        sdk_path = sh.xcrun(
            "--sdk", "macosx",
            "--show-sdk-path").splitlines()[0]

        build_env = self.ctx.env.copy()
        build_env["CC"] = "clang -Qunused-arguments -fcolor-diagnostics"
        build_env["LDFLAGS"] = "-lsqlite3"
        build_env["CFLAGS"] = "--sysroot={}".format(sdk_path)
        build_env["PWD"] = self.build_dir
        configure = sh.Command(join(self.build_dir, "configure"))
        print "-->"
        shprint(configure, _env=build_env)
        sh.make("-C", self.build_dir, "-j4", "python.exe", "Parser/pgen")
        print "<--"




recipe = HostpythonRecipe()
