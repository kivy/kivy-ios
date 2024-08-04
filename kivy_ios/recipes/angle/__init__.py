import os
import shutil

from kivy_ios.toolchain import GenericPlatform, Recipe, cache_execution, logger


class IphoneAllUniversalPlatform(GenericPlatform):

    @property
    def name(self):
        return "iphoneall-universal"


class ANGLERecipe(Recipe):
    version = "chromium-6367_rev1"
    url = "https://github.com/kivy/angle-builder/releases/download/{version}/angle-iphoneall-universal.tar.gz"
    include_dir = ["include"]
    libraries = ["libEGL.a", "libGLESv2.a"]

    @property
    def platforms_to_build(self):
        yield IphoneAllUniversalPlatform(self.ctx)

    @cache_execution
    def build_all(self):
        self.install_include()
        self.install()

    @cache_execution
    def install(self):
        xcframework_folder = os.path.join(self.ctx.dist_dir, "xcframework")

        build_dir = self.get_build_dir(
            plat=IphoneAllUniversalPlatform(self.ctx)
        )

        for fn in os.listdir(build_dir):
            if fn.endswith(".xcframework"):
                shutil.copytree(
                    os.path.join(build_dir, fn),
                    os.path.join(xcframework_folder, fn),
                    dirs_exist_ok=True
                )


recipe = ANGLERecipe()
