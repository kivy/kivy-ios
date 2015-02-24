from toolchain import Recipe, shprint
from os.path import join
import sh
import os
import shutil


class AudiostreamRecipe(Recipe):
    version = "master"
    url = "https://github.com/kivy/audiostream/archive/{version}.zip"
    library = "libaudiostream.a"
    depends = ["python", "sdl2"]

    def get_kivy_env(self, arch):
        build_env = arch.get_env()
        build_env["KIVYIOSROOT"] = self.ctx.root_dir
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["CC"] = "{} -I{}".format(
                build_env["CC"],
                join(self.ctx.dist_dir, "include", "common", "sdl2"))
        build_env["ARCH"] = arch.arch
        return build_env

    def build_arch(self, arch):
        build_env = self.get_kivy_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        try:
            shprint(hostpython, "setup.py", "build_ext", "-g",
                    _env=build_env)
        except:
            pass
        self.cythonize_build()
        shprint(hostpython, "setup.py", "build_ext", "-g",
                _env=build_env)
        self.biglink()

    def install(self):
        arch = list(self.filtered_archs)[0]
        build_dir = self.get_build_dir(arch.arch)
        os.chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)
        build_env = self.get_kivy_env(arch)
        shprint(hostpython, "setup.py", "install", "-O2",
                "--prefix", join(build_dir, "iosbuild"),
                _env=build_env)
        dest_dir = join(self.ctx.dist_dir, "root", "python", "lib", "python2.7",
                "site-packages", "audiostream")
        shutil.copytree(
            join(build_dir, "iosbuild", "lib",
                 "python2.7", "site-packages", "audiostream"),
            dest_dir)

recipe = AudiostreamRecipe()


