from toolchain import CythonRecipe, shprint
from os.path import join
from os import chdir, listdir, getcwd
import sh
import logging

logger = logging.getLogger(__name__)


class KivyRecipe(CythonRecipe):
    version = "1.11.0"
    url = "https://github.com/kivy/kivy/archive/{version}.zip"
    library = "libkivy.a"
    depends = ["sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "ios",
               "pyobjus", "python"]
    pbx_frameworks = ["OpenGLES", "Accelerate", "CoreMedia", "CoreVideo"]
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
        with open(pyconfig, "w") as fd:
            fd.writelines(lines)

    def install_python_package(self, name=None, env=None, is_dir=True):
        """
        Automate the installation of a Python package into the target
        site-packages.
        """
        arch = self.filtered_archs[0]
        if name is None:
            name = self.name
        if env is None:
            env = self.get_recipe_env(arch)
        print("Install {} into the site-packages".format(name))
        build_dir = self.get_build_dir(arch.arch)
        chdir(build_dir)

        hostpython = sh.Command(self.ctx.hostpython)
        env["PYTHONPATH"] = self.ctx.site_packages_dir
        shprint(
            hostpython,
            "setup.py",
            "bdist_egg",
            "--exclude-source-files",
            "--plat-name=",
            # "--plat-name={}".format(arch.arch),
            _env=env,
        )
        for file in listdir("./dist"):
            if file.endswith(".egg"):
                egg_name = file
        shprint(
            hostpython,
            "setup.py",
            "easy_install",
            "--no-deps",
            "--install-dir",
            self.ctx.site_packages_dir,
            join("dist", egg_name),
            _env=env,
        )

        # clean
        oldpwd = getcwd()
        try:
            logger.info("Remove files unlikely to be used")
            chdir(join(self.ctx.site_packages_dir, egg_name))
            sh.rm("-rf", "share")
            sh.rm("-rf", "kivy/tools")
            sh.rm("-rf", "kivy/tests")
        finally:
            chdir(oldpwd)


recipe = KivyRecipe()
