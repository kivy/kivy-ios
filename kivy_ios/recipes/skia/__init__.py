import os
import shutil
import sh

from kivy_ios.toolchain import Recipe, cache_execution, shprint


class LibSkiaRecipe(Recipe):
    version = "skia-binaries-m138-rev2.a0"
    url = "https://github.com/DexerBR/skia-builder/releases/download/{version}/{plat_arch}.tar.gz"
    skia_libraries = [
        "libskresources.a",
        "libskparagraph.a",
        "libskia.a",
        "libskottie.a",
        "libsvg.a",
        "libsksg.a",
        "libskshaper.a",
        "libskunicode_icu.a",
        "libskunicode_core.a",
        "libjsonreader.a",
    ]
    libraries = [
        "libskmerged.a",
    ]

    def build_all(self):
        self.build()
        self.create_xcframeworks()
        self.install()

    def download(self):
        pass

    def extract_platform(self, plat):
        pass

    def _get_skia_platform(self, plat):
        if plat.name == "iphonesimulator-arm64":
            return "iossimulator-arm64"
        elif plat.name == "iphonesimulator-x86_64":
            return "iossimulator-x64"
        elif plat.name == "iphoneos-arm64":
            return "ios-arm64"

    @cache_execution
    def build(self):
        first_platform = True
        for plat in self.platforms_to_build:
            # Get the platform-specific Skia directory
            skia_platform = self._get_skia_platform(plat)

            # Define the build directory for the platform
            build_main_dir = os.path.join(self.ctx.build_dir, "skia", plat.name)

            # Create the build directory if it doesn't exist
            if not os.path.exists(os.path.join(build_main_dir)):
                os.makedirs(build_main_dir)

            # Create the download directory if it doesn't exist
            download_dir = os.path.join(build_main_dir, "download")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

            # Create the unpack directory if it doesn't exist
            unpack_dir = os.path.join(build_main_dir, "unpacked")
            if not os.path.exists(unpack_dir):
                os.makedirs(unpack_dir)

            fn = os.path.join(
                download_dir, f"skia-{self.version}-{skia_platform}.tar.gz"
            )

            self.download_file(
                self.url.format(version=self.version, plat_arch=skia_platform),
                fn,
            )

            self.extract_file(fn, unpack_dir)

            dist_lib_dir = os.path.join(self.ctx.dist_dir, "lib", plat.sdk)

            # Add .a libraries to the distribution directory
            static_libs = [
                f
                for f in os.listdir(os.path.join(unpack_dir, "bin"))
                if f.endswith(".a")
            ]

            for lib in static_libs:
                lib_path = os.path.join(unpack_dir, "bin", lib)
                library_fn = os.path.basename(lib_path)
                dest_path = os.path.join(dist_lib_dir, library_fn)

                if not os.path.exists(dist_lib_dir):
                    os.makedirs(dist_lib_dir)

                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(lib_path, dest_path)

            # Merge the static libraries into a single library
            merged_lib_path = os.path.join(dist_lib_dir, "libskmerged.a")
            if os.path.exists(merged_lib_path):
                os.remove(merged_lib_path)

            # Extract all the self.skia_libraries via ar x
            for lib in self.skia_libraries:
                lib_path = os.path.join(dist_lib_dir, lib)
                if not os.path.exists(lib_path):
                    raise FileNotFoundError(f"Library {lib} not found in {dist_lib_dir}")

                # Extract the library using ar
                ar_cmd = [
                    sh.Command("ar"),
                    "x",
                    lib_path,
                ]
                shprint(*ar_cmd, _cwd=dist_lib_dir)

            #

            # Use libtool to merge the libraries
            libtool_cmd = (
                [
                    sh.Command("libtool"),
                    "-static",
                ]
                + ["-o", merged_lib_path]
                + [
                    os.path.join(dist_lib_dir, lib)
                    for lib in self.skia_libraries
                ]
            )

            shprint(*libtool_cmd)

            if not first_platform:
                first_platform = False
                continue

            for skia_src in ["include", "modules", "src"]:
                # Add include files to the distribution directory
                include_dir = os.path.join(unpack_dir, skia_src)
                dist_include_dir = os.path.join(
                    self.ctx.dist_dir, "include", "common", "skia", skia_src
                )

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
