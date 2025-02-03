from kivy_ios.toolchain import CythonRecipe
from os.path import join


class FFPyplayerRecipe(CythonRecipe):
    version = "v4.3.5"
    url = "https://github.com/matham/ffpyplayer/archive/{version}.zip"
    library = "libffpyplayer.a"
    depends = ["python", "sdl2", "ffmpeg"]
    pbx_frameworks = [
        "CoreVideo", "CoreMedia", "CoreImage", "AVFoundation", "UIKit",
        "CoreMotion"]
    pbx_libraries = ["libiconv"]
    pre_build_ext = True
    hostpython_prerequisites = ["Cython==0.29.37"]

    def get_recipe_env(self, plat):
        env = super(FFPyplayerRecipe, self).get_recipe_env(plat)
        env["CC"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", plat.name, "libffi"))
        env["SDL_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include",
                                      "common", "sdl2")
        env["FFMPEG_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include",
                                         plat.name, "ffmpeg")
        env["CONFIG_POSTPROC"] = "0"
        return env

    def prebuild_platform(self, plat):
        # common to all archs
        if self.has_marker("patched"):
            return
        self.apply_patch("misc-visibility.patch")
        self.set_marker("patched")


recipe = FFPyplayerRecipe()
