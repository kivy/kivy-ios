import os
import shutil
import sh

from kivy_ios.toolchain import Recipe, shprint


class LibSkiaRecipe(Recipe):
    version = "skia-binaries-m138-rev3.a0"
    url = "https://github.com/DexerBR/skia-builder/releases/download/{version}/ios-merged.tar.gz"
    skia_libraries = [
        # "libskresources.a",
        "libskparagraph.a",
        "libskia.a",
        "libskottie.a",
        # "libsvg.a",
        "libsksg.a",
        "libskshaper.a",
        "libskunicode_icu.a",
        "libskunicode_core.a",
        "libjsonreader.a",
    ]
    libraries = [
        "dist/libskmerged.a",
    ]

    include_dir = [
        "dist/include_dirs",
    ]

    include_per_platform = True

    def _get_skia_platform(self, plat):
        if plat.name == "iphonesimulator-arm64":
            return "iossimulator-arm64"
        elif plat.name == "iphonesimulator-x86_64":
            return "iossimulator-x64"
        elif plat.name == "iphoneos-arm64":
            return "ios-arm64"

    def build_platform(self, plat):

        build_dir = self.get_build_dir(plat)

        # Get the Skia platform name
        skia_platform = self._get_skia_platform(plat)

        # Create the unpack directory if it doesn't exist
        unpack_dir = os.path.join(build_dir, "unpacked")
        if not os.path.exists(unpack_dir):
            os.makedirs(unpack_dir)

        # Create the dist directory in build_dir if it doesn't exist
        skia_dist_dir = os.path.join(build_dir, "dist")
        if not os.path.exists(skia_dist_dir):
            os.makedirs(skia_dist_dir)

        skia_binaries_archive = os.path.join(
            build_dir, f"{skia_platform}.tar.gz"
        )

        self.extract_file(skia_binaries_archive, unpack_dir)

        # Merge the static libraries into a single library
        merged_lib_path = os.path.join(skia_dist_dir, "libskmerged.a")

        # Use libtool to merge the libraries
        libtool_cmd = (
            [
                sh.Command("libtool"),
                "-static",
            ]
            + ["-o", merged_lib_path]
            + [
                os.path.join("unpacked", "bin", lib)
                for lib in self.skia_libraries
            ]
        )
        shprint(*libtool_cmd)

        for skia_src in ["include", "modules", "src"]:
            # Add include files to the distribution directory
            include_dir = os.path.join(unpack_dir, skia_src)
            dist_include_dir = os.path.join(skia_dist_dir, "include_dirs", skia_src)

            if os.path.exists(dist_include_dir):
                shutil.rmtree(dist_include_dir)

            if not os.path.exists(dist_include_dir):
                os.makedirs(dist_include_dir)

            # Copy all the files and directories from include_dir to dist_include_dir
            for item in os.listdir(include_dir):
                s = os.path.join(include_dir, item)
                d = os.path.join(dist_include_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)


recipe = LibSkiaRecipe()
