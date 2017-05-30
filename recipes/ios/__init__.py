from toolchain import CythonRecipe


class IosRecipe(CythonRecipe):
    version = "master"
    url = "src"
    library = "libios.a"
    depends = ["python"]
    pbx_frameworks = ["MessageUI", "CoreMotion", "UIKit"]

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

    def install(self):
        self.install_python_package(name="ios.so", is_dir=False)


recipe = IosRecipe()


