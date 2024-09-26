from kivy_ios.toolchain import CythonRecipe
from os.path import join
import logging
import shutil

logger = logging.getLogger(__name__)


class KivyRecipe(CythonRecipe):
    version = "master"
    url = "https://github.com/kivy/kivy/archive/{version}.zip"
    library = "libkivy.a"
    depends = ["angle", "sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "ios",
               "pyobjus", "python"]
    python_depends = ["certifi", "charset-normalizer", "idna", "requests", "urllib3", "filetype"]
    pbx_frameworks = ["Accelerate", "CoreMedia", "CoreVideo", "Metal", "UniformTypeIdentifiers"]
    pre_build_ext = True

    def get_recipe_env(self, plat):
        env = super().get_recipe_env(plat)
        env["KIVY_SDL2_PATH"] = ":".join([
            join(self.ctx.dist_dir, "include", "common", "sdl2"),
            join(self.ctx.dist_dir, "include", "common", "sdl2_image"),
            join(self.ctx.dist_dir, "include", "common", "sdl2_ttf"),
            join(self.ctx.dist_dir, "include", "common", "sdl2_mixer")])
        env["KIVY_ANGLE_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include", "common", "angle")
        env["KIVY_ANGLE_LIB_DIR"] = join(self.ctx.dist_dir, "frameworks", plat.sdk)
        return env

    def reduce_python_package(self):
        dest_dir = join(self.ctx.site_packages_dir, "kivy")
        shutil.rmtree(join(dest_dir, "tools"))
        shutil.rmtree(join(dest_dir, "tests"))


recipe = KivyRecipe()
