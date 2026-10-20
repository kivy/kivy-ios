from kivy_ios.toolchain import MesonRecipe, Recipe
from os.path import join, exists


class PycairoRecipe(MesonRecipe):
    name = "pycairo"
    version = "1.28.0"
    url = "https://github.com/pygobject/pycairo/releases/download/v{version}/pycairo-{version}.tar.gz"
    library = "libpycairo.a"
    include_dir = "builddir/install/include/pycairo"
    depends = ["hostpython3", "python3", "libcairo"]
    patches = ["meson.patch"]
    skip_python = False
    site_packages_name = "cairo"

    def get_recipe_meson_options(self, plat):
        cairo_include = join(self.ctx.include_dir, "common", "cairo")
        if not exists(cairo_include):
            cairo_include = join(self.ctx.include_dir, "common", "libcairo")
        if not exists(cairo_include):
            cairo_include = join(self.ctx.include_dir, plat.name, "cairo")
        if not exists(cairo_include):
            libcairo_recipe = Recipe.get_recipe("libcairo", self.ctx)
            cairo_include = join(
                self.ctx.build_dir, "libcairo", plat.name,
                f"cairo-{libcairo_recipe.version}",
                "builddir", "install", "include", "cairo"
            )

        cairo_lib = join(self.ctx.dist_dir, "lib", plat.sdk)

        return [
            f"-Dcairo_include={cairo_include}",
            f"-Dcairo_lib={cairo_lib}",
            "-Dtests=false",
        ]


recipe = PycairoRecipe()
