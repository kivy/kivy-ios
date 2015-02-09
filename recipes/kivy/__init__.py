from toolchain import Recipe, shprint
from os.path import join
import sh
import os
import fnmatch


class KivyRecipe(Recipe):
    version = "master"
    url = "https://github.com/kivy/kivy/archive/{version}.zip"
    #library = "Xcode-iOS/build/Release-{arch.sdk}/libSDL2_image.a"
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

    def build_arch(self, arch):
        build_env = arch.get_env()
        build_env["KIVYIOSROOT"] = self.ctx.root_dir
        build_env["IOSSDKROOT"] = arch.sysroot
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
        import sys
        sys.exit(0)


recipe = KivyRecipe()


