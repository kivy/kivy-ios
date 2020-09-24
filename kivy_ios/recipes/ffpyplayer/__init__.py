from kivy_ios.toolchain import CythonRecipe
from os.path import join


class FFPyplayerRecipe(CythonRecipe):
    version = "4.2.0"
    url = "https://github.com/matham/ffpyplayer/archive/{version}.zip"
    library = "libffpyplayer.a"
    depends = ["python", "ffmpeg"]
    pbx_frameworks = [
        "CoreVideo", "CoreMedia", "CoreImage", "AVFoundation", "UIKit",
        "CoreMotion"]
    pbx_libraries = ["libiconv"]
    pre_build_ext = True

    def get_recipe_env(self, arch):
        env = super(FFPyplayerRecipe, self).get_recipe_env(arch)
        env["CC"] += " -I{}".format(
            join(self.ctx.dist_dir, "include", arch.arch, "libffi"))
        env["SDL_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include",
                                      "common", "sdl2")
        env["FFMPEG_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include",
                                         arch.arch, "ffmpeg")
        env["CONFIG_POSTPROC"] = "0"
        return env

    def prebuild_arch(self, arch):
        # common to all archs
        if self.has_marker("patched"):
            return
        self.apply_patch("misc-visibility.patch")
        self.set_marker("patched")


recipe = FFPyplayerRecipe()
