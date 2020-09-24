from kivy_ios.toolchain import Recipe, shprint
from os.path import join
import sh


class LibZBarRecipe(Recipe):

    version = '0.10'

    url = 'https://github.com/ZBar/ZBar/archive/{version}.zip'

    depends = ['hostpython3']

    library = 'zbar/.libs/libzbar.a'

    include_per_arch = True
    include_dir = [
        ("include", "")
        ]

    def prebuild_arch(self, arch):
        if self.has_marker("patched"):
            return
        self.apply_patch("werror.patch")
        self.set_marker("patched")

    def build_arch(self, arch):
        super(LibZBarRecipe, self).build_arch(arch)
        build_env = arch.get_env()
        build_env["CFLAGS"] = " ".join([
            "-I{}".format(join(self.ctx.dist_dir, "build", "libiconv", arch.arch)) +
            " -arch {}".format(arch.arch), build_env['CFLAGS']
            ])
        shprint(sh.Command('autoreconf'), '-vif')
        shprint(
            sh.Command('./configure'),
            "CC={}".format(build_env["CC"]),
            "LD={}".format(build_env["LD"]),
            "CFLAGS={}".format(build_env["CFLAGS"]),
            "LDFLAGS={}".format(build_env["LDFLAGS"]),
            "--host={}".format(arch.triple),
            '--target={}'.format(arch.triple),
            # Python bindings are compiled in a separated recipe
            '--with-python=no',
            '--with-gtk=no',
            '--with-qt=no',
            '--with-x=no',
            '--with-jpeg=no',
            '--with-imagemagick=no',
            '--enable-pthread=no',
            '--enable-video=no',
            "--disable-shared",
            _env=build_env)
        shprint(sh.make, 'clean')
        shprint(sh.make, _env=build_env)


recipe = LibZBarRecipe()
