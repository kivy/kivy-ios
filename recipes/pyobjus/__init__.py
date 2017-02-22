from toolchain import CythonRecipe, shprint
from os.path import join
from os import walk
import fnmatch
import sh


class PyobjusRecipe(CythonRecipe):
    version = "master"
    url = "https://github.com/kivy/pyobjus/archive/{version}.zip"
    library = "libpyobjus.a"
    depends = ["python"]
    pre_build_ext = True

    def prebuild_arch(self, arch):
        from os.path import join
        destdir = self.get_build_dir(arch.arch)
        local_arch = arch.arch
        if arch.arch == "arm64" :
            local_arch = "aarch64"
        if arch.arch == "armv7" :
            local_arch = "arm"
        build_dir = join(destdir, "../../../python", arch.arch, "Python-2.7.13", "build", "lib.darwin-{}-2.7".format(local_arch))
        print("build_dir = "+build_dir)
        copyfile = join(build_dir,"_sysconfigdata.py")
        # Copy _sysconfigdata.py for this architecture across
        self.copy_file(copyfile,destdir)

    def get_recipe_env(self, arch):
        env = super(PyobjusRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
                join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        return env

    def cythonize_file(self, filename):
        if filename.startswith(self.build_dir):
            filename = filename[len(self.build_dir) + 1:]
        print("Cython {}".format(filename))
        cmd = sh.Command("/usr/local/bin/cython")
        shprint(cmd, filename)

    def cythonize_build(self):
        if not self.cythonize:
            return
        root_dir = self.build_dir

        for root, dirnames, filenames in walk(root_dir):
            #print(filenames)
            for filename in fnmatch.filter(filenames, "*.pyx"):
                #print("DBJ pyx files "+filename)
                #shprint(cmd, filename)
                self.cythonize_file(join(root, filename))
        # ffi is installed somewhere else, this include doesn't work
        # XXX ideally, we need to fix libffi installation...
        shprint(sh.sed,
                "-i.bak",
                "s/ffi\///g",
                "pyobjus/pyobjus.c")

recipe = PyobjusRecipe()


