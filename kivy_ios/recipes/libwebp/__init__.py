from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class WebpRecipe(Recipe):
    version = '1.0.3'
    url = 'https://github.com/webmproject/libwebp/archive/v{version}.zip'

    def build_arch(self, arch):
        # build_env = arch.get_env()
        iosbuild = sh.Command(join(self.build_dir, "iosbuild.sh"))
        shprint(iosbuild)


recipe = WebpRecipe()
