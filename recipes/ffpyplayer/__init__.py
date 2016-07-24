from toolchain import CythonRecipe, shprint
from os.path import join
import sh


class FFPyplayerRecipe(CythonRecipe):
    version = "v3.2"
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


recipe = FFPyplayerRecipe()

