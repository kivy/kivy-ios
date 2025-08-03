import logging
import os
import shutil
import sys
import tempfile

from os.path import join

import packaging.version
import sh

from kivy_ios.toolchain import CythonRecipe

logger = logging.getLogger(__name__)


class KivyRecipe(CythonRecipe):
    version = "2.3.1"
    # url = "https://github.com/kivy/kivy/archive/{version}.zip"
    url = "https://github.com/DexerBr/kivy/archive/refs/heads/pure_skia_tests.zip"
    # url = "https://github.com/misl6/kivy/archive/refs/heads/fix-typo-skia-include-dirs.zip"
    library = "libkivy.a"
    _base_depends = ["ios", "pyobjus", "python"]
    python_depends = [
        "certifi",
        "charset-normalizer",
        "idna",
        "requests",
        "urllib3",
        "filetype",
    ]
    _base_pbx_frameworks = [
        "Accelerate",
        "CoreMedia",
        "CoreVideo",
        "AVFoundation",
    ]
    pre_build_ext = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required_sdl_version = None

    def get_required_sdl_version(self):
        """
        Determine the SDL version required by the Kivy version.
        Returns 'sdl2' for Kivy versions < 2.3.0, and 'sdl3' for Kivy >= 2.3.0.
        """
        if self._required_sdl_version is not None:
            return self._required_sdl_version

        # Download and extract Kivy source to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = join(temp_dir, "kivy.zip")
            self.download_file(
                self.url.format(version=self.version), archive_path
            )
            self.extract_file(archive_path, temp_dir)

            # Locate the extracted Kivy folder
            kivy_folders = [
                f
                for f in os.listdir(temp_dir)
                if os.path.isdir(os.path.join(temp_dir, f))
            ]
            kivy_dir = os.path.join(temp_dir, kivy_folders[0], "kivy")

            # Get Kivy version by running a subprocess
            cur_dir = os.getcwd()
            try:
                os.chdir(kivy_dir)
                cmd = sh.Command(sys.executable)
                kivy_version_str = cmd(
                    "-c",
                    "import _version; print(_version.__version__)",
                ).strip()
            finally:
                os.chdir(cur_dir)

            kivy_version = packaging.version.parse(str(kivy_version_str))
            self._required_sdl_version = (
                "sdl2"
                if kivy_version < packaging.version.parse("3.0.0.dev0")
                else "sdl3"
            )

        return self._required_sdl_version

    @property
    def pbx_frameworks(self):
        if self.get_required_sdl_version() == "sdl2":
            return self._base_pbx_frameworks + [
                "OpenGLES",
            ]
        elif self.get_required_sdl_version() == "sdl3":
            return self._base_pbx_frameworks + [
                "Metal",
            ]
        else:
            raise ValueError(
                f"Unsupported SDL version: {self.get_required_sdl_version()}"
            )

    @property
    def depends(self):
        if self.get_required_sdl_version() == "sdl2":
            return self._base_depends + [
                "sdl2",
                "sdl2_image",
                "sdl2_ttf",
                "sdl2_mixer",
            ]
        elif self.get_required_sdl_version() == "sdl3":
            return self._base_depends + [
                "skia",
                "sdl3",
                "sdl3_image",
                "sdl3_ttf",
                "sdl3_mixer",
                "angle",
            ]
        else:
            raise ValueError(
                f"Unsupported SDL version: {self.get_required_sdl_version()}"
            )

    def get_recipe_env(self, plat):
        env = super().get_recipe_env(plat)
        if self.get_required_sdl_version() == "sdl2":
            env["KIVY_SDL2_PATH"] = ":".join(
                [
                    join(self.ctx.dist_dir, "include", "common", "sdl2"),
                    join(self.ctx.dist_dir, "include", "common", "sdl2_image"),
                    join(self.ctx.dist_dir, "include", "common", "sdl2_ttf"),
                    join(self.ctx.dist_dir, "include", "common", "sdl2_mixer"),
                ]
            )
        elif self.get_required_sdl_version() == "sdl3":
            env["SKIA_LIB_DIR"] = "/fake/path/to/skia/libs"
            env["SKIA_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include", plat.name, "skia")
            env["KIVY_ANGLE_INCLUDE_DIR"] = join(self.ctx.dist_dir, "include", "common", "angle")
            env["KIVY_ANGLE_LIB_DIR"] = join(self.ctx.dist_dir, "frameworks", plat.sdk)
            env["KIVY_SDL3_PATH"] = ":".join(
                [
                    join(self.ctx.dist_dir, "include", "common", "sdl3"),
                    join(
                        self.ctx.dist_dir, "include", "common", "sdl3", "SDL3"
                    ),
                    join(self.ctx.dist_dir, "include", "common", "sdl3_image"),
                    join(
                        self.ctx.dist_dir,
                        "include",
                        "common",
                        "sdl3_image",
                        "SDL3_image",
                    ),
                    join(self.ctx.dist_dir, "include", "common", "sdl3_ttf"),
                    join(
                        self.ctx.dist_dir,
                        "include",
                        "common",
                        "sdl3_ttf",
                        "SDL3_ttf",
                    ),
                    join(self.ctx.dist_dir, "include", "common", "sdl3_mixer"),
                    join(
                        self.ctx.dist_dir,
                        "include",
                        "common",
                        "sdl3_mixer",
                        "SDL3_mixer",
                    ),
                ]
            )
        return env

    def build_platform(self, plat):
        if self.get_required_sdl_version() == "sdl2":
            self._patch_setup()
        super().build_platform(plat)

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
        with open(pyconfig, "w") as fd:
            fd.writelines(lines)

    def reduce_python_package(self):
        dest_dir = join(self.ctx.site_packages_dir, "kivy")
        shutil.rmtree(join(dest_dir, "tools"))
        shutil.rmtree(join(dest_dir, "tests"))


recipe = KivyRecipe()
