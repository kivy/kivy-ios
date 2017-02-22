from toolchain import CythonRecipe
from os.path import join


class KivyRecipe(CythonRecipe):
    version = "1.9.1"
    url = "https://github.com/kivy/kivy/archive/{version}.zip"
    library = "libkivy.a"
    depends = ["python", "sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "ios",
               "pyobjus"]
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

    def prebuild_arch(self, arch):
        from os.path import join
        destdir = self.get_build_dir(arch.arch)
        local_arch = arch.arch
        if arch.arch == "arm64" :
            local_arch = "aarch64"
        if arch.arch == "armv7" :
            local_arch = "arm"
        build_dir = join(destdir, "../../../python", arch.arch, "Python-2.7.13", "build", "lib.darwin-{}-2.7".format(local_arch))
        print("build_dir = "+build_dir)
        copyfile = join(build_dir,"_sysconfigdata.py")
        # Copy _sysconfigdata.py for this architecture across
        self.copy_file(copyfile,destdir)

    def build_arch(self, arch):
        self._patch_setup()
        super(KivyRecipe, self).build_arch(arch)

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

