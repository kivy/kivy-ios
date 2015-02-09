from toolchain import Recipe, shprint
from os.path import join
import sh
import shutil


class HostpythonRecipe(Recipe):
    version = "2.7.1"
    url = "https://www.python.org/ftp/python/{version}/Python-{version}.tar.bz2"
    depends = ["libffi", ]
    archs = ["i386"]

    def download(self):
        super(HostpythonRecipe, self).download()
        self.ctx.hostpython = join(
                self.ctx.build_dir, self.name, "i386", self.archive_root,
                "hostpython")
        self.ctx.hostpgen = join(
                self.ctx.build_dir, self.name, "i386", self.archive_root,
                "Parser", "hostpgen")
        print("Global: hostpython located at {}".format(self.ctx.hostpython))
        print("Global: hostpgen located at {}".format(self.ctx.hostpgen))

    def prebuild_arch(self, arch):
        if  self.has_marker("patched"):
            return
        self.apply_patch("ssize-t-max.patch")
        self.apply_patch("dynload.patch")
        self.apply_patch("static-_sqlite3.patch")
        self.copy_file("ModulesSetup", "Modules/Setup.local")
        self.set_marker("patched")

    def postbuild_arch(self, arch):
        makefile_fn = join(self.build_dir, "Makefile")
        with open(makefile_fn) as fd:
            lines = fd.readlines()
        for index, line in enumerate(lines):
            if "-bundle" not in line:
                continue
            parts = line.split(" ")
            parts.remove("-bundle")
            if "-bundle_loader" in parts:
                i = parts.index("-bundle_loader")
                parts.pop(i)
                parts.pop(i)
            lines[index] = " ".join(parts)
        with open(makefile_fn, "w") as fd:
            fd.writelines(lines)

    def build_i386(self):
        sdk_path = sh.xcrun("--sdk", "macosx", "--show-sdk-path").strip()

        build_env = self.ctx.env.copy()
        build_env["CC"] = "clang -Qunused-arguments -fcolor-diagnostics"
        build_env["LDFLAGS"] = "-lsqlite3"
        build_env["CFLAGS"] = "--sysroot={}".format(sdk_path)
        configure = sh.Command(join(self.build_dir, "configure"))
        shprint(configure, _env=build_env)
        shprint(sh.make, "-C", self.build_dir, "-j4", "python.exe", "Parser/pgen",
                _env=build_env)
        shutil.move("python.exe", "hostpython")
        shutil.move("Parser/pgen", "Parser/hostpgen")

recipe = HostpythonRecipe()
