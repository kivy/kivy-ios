from toolchain import Recipe, shprint
from os.path import join, exists
import sh
import os
import fnmatch
import shutil


class KivyRecipe(Recipe):
    version = "master"
    url = "https://github.com/kivy/kivy/archive/{version}.zip"
    library = "libkivy.a"
    #include_dir = "SDL_image.h"
    depends = ["python", "sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf"]

    def cythonize(self, filename):
        if filename.startswith(self.build_dir):
            filename = filename[len(self.build_dir) + 1:]
        print("Cythonize {}".format(filename))
        cmd = sh.Command(join(self.ctx.root_dir, "tools", "cythonize.py"))
        shprint(cmd, filename)

    def cythonize_build(self):
        root_dir = join(self.build_dir, "kivy")
        for root, dirnames, filenames in os.walk(root_dir):
            for filename in fnmatch.filter(filenames, "*.pyx"):
                self.cythonize(join(root, filename))

    def get_kivy_env(self, arch):
        build_env = arch.get_env()
        build_env["KIVYIOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
        build_env["LDSHARED"] = join(self.ctx.root_dir, "tools", "liblink")
        build_env["ARM_LD"] = build_env["LD"]
        build_env["ARCH"] = arch.arch
        build_env["KIVY_SDL2_PATH"] = join(self.ctx.dist_dir, "include", "common", "sdl2")
        return build_env

    def build_arch(self, arch):
        self._patch_setup()
        build_env = self.get_kivy_env(arch)
        hostpython = sh.Command(self.ctx.hostpython)
        # first try to generate .h
        try:
            shprint(hostpython, "setup.py", "build_ext", "-g",
                    _env=build_env)
        except:
            pass
        self.cythonize_build()
        shprint(hostpython, "setup.py", "build_ext", "-g",
                _env=build_env)
        self.biglink()

    def biglink(self):
        dirs = []
        for root, dirnames, filenames in os.walk(self.build_dir):
            if fnmatch.filter(filenames, "*.so.libs"):
                dirs.append(root)
        cmd = sh.Command(join(self.ctx.root_dir, "tools", "biglink"))
        shprint(cmd, join(self.build_dir, "libkivy.a"), *dirs)

    def _patch_setup(self):
        # patch setup to remove some functionnalities
        pyconfig = join(self.build_dir, "setup.py")
        def _remove_line(lines, pattern):
            for line in lines[:]:
                if pattern in line:
                    lines.remove(line)
        with open(pyconfig) as fd:
            lines = fd.readlines()
        _remove_line(lines, "flags['libraries'] = ['GLESv2']")
        #_remove_line(lines, "c_options['use_sdl'] = True")
        with open(pyconfig, "wb") as fd:
            fd.writelines(lines)

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
                "site-packages", "kivy")
        if exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.copytree(
            join(build_dir, "iosbuild", "lib",
                 "python2.7", "site-packages", "kivy"),
            dest_dir)

recipe = KivyRecipe()


