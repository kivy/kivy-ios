from kivy_ios.toolchain import MesonRecipe, ensure_dir
from os.path import join, exists
from contextlib import suppress


class LibcairoRecipe(MesonRecipe):
    name = "libcairo"
    version = "1.18.4"
    url = "https://gitlab.freedesktop.org/cairo/cairo/-/archive/{version}/cairo-{version}.tar.bz2"
    library = "builddir/src/libcairo.a"
    include_dir = "builddir/install/include/cairo"
    include_name = "cairo"
    depends = ["hostpython3", "libpng"]
    patches = ["meson.patch"]
    skip_python = True

    pixman_version = "0.43.4"
    pixman_urls = [
        "https://www.cairographics.org/releases/pixman-{version}.tar.gz",
        "https://github.com/mesonbuild/wrapdb/releases/download/pixman_{version}-1/pixman-{version}.tar.gz",
    ]

    def prebuild_platform(self, plat):
        super().prebuild_platform(plat)
        build_dir = self.build_dir if hasattr(self, "build_dir") and self.build_dir else self.get_build_dir(plat)
        cache_dir = join(build_dir, "subprojects", "packagecache")
        ensure_dir(cache_dir)
        pixman_tar = join(cache_dir, f"pixman-{self.pixman_version}.tar.gz")
        if not exists(pixman_tar):
            for url in self.pixman_urls:
                with suppress(Exception):
                    self.download_file(
                        url.format(version=self.pixman_version),
                        f"pixman-{self.pixman_version}.tar.gz",
                        cwd=cache_dir,
                    )
                    if exists(pixman_tar):
                        break

    def get_recipe_meson_options(self, plat):
        png_include = join(self.ctx.include_dir, "common", "libpng")
        if not exists(png_include):
            png_include = join(self.ctx.include_dir, plat.name, "libpng")

        lib_dir = join(self.ctx.dist_dir, "lib", plat.sdk)

        return [
            "-Dpng=enabled",
            "-Dzlib=enabled",
            "-Dglib=disabled",
            "-Dfreetype=disabled",
            "-Dfontconfig=disabled",
            "-Dquartz=disabled",
            "-Dtests=disabled",
            "-Dspectre=disabled",
            "-Dgtk_doc=false",
            "-Dsymbol-lookup=disabled",
            "-Dpixman:tests=disabled",
            "-Dpixman:demos=disabled",
            # deps
            f"-Dpng_include_dir={png_include}",
            f"-Dpng_lib_dir={lib_dir}",
        ]


recipe = LibcairoRecipe()
