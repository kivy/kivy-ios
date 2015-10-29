from toolchain import CythonRecipe
from os.path import join

from sys import stdout
import sh

def shprint(command, *args, **kwargs):
    kwargs["_iter"] = True
    kwargs["_out_bufsize"] = 1
    kwargs["_err_to_out"] = True
    for line in command(*args, **kwargs):
        stdout.write(line)


class KivyRecipe(CythonRecipe):
    version = "1.9.0"
    url = "https://github.com/kivy/kivy/archive/{version}.zip"
    library = "libkivy.a"
    depends = ["python", "sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "ios"]
    pbx_frameworks = ["OpenGLES", "Accelerate"]
    pre_build_ext = True

    def get_recipe_env(self, arch):
        env = super(KivyRecipe, self).get_recipe_env(arch)
        env["KIVY_SDL2_PATH"] = ":".join([
            join(self.ctx.dist_dir, "include", "common", "sdl2"),
            join(self.ctx.dist_dir, "include", "common", "sdl2_image"),
            join(self.ctx.dist_dir, "include", "common", "sdl2_ttf"),
            join(self.ctx.dist_dir, "include", "common", "sdl2_mixer")])
        return env

    def build_arch(self, arch):
        self._patch_setup()
        build_env = self.get_recipe_env(arch)
        build_env["PYTHONHOME"] = join(self.ctx.dist_dir, "hostpython")
        #print 'build_env=', build_env
        hostpython = sh.Command(self.ctx.hostpython)
        #hostpython = sh.Command("/usr/bin/python2.7")
        if self.pre_build_ext:
            try:
                shprint(hostpython, "setup.py", "build_ext", "-g",
                        _env=build_env)
            except:
                pass
        self.cythonize_build()
        shprint(hostpython, "setup.py", "build_ext", "-g",
                _env=build_env)
        self.biglink()

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


recipe = KivyRecipe()

