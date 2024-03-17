from kivy_ios.toolchain import PythonRecipe


class MaterialYouColorRecipe(PythonRecipe):
    version = "2.0.7"
    url = "https://github.com/T-Dynamos/materialyoucolor-pyhton/archive/refs/tags/v{version}.tar.gz"
    depends = ["hostpython3", "python3"]
    hostpython_prerequisites = ["certifi"]

    def prebuild_platform(self, plat):
        if self.has_marker("patched"):
            return
        self.apply_patch("fix_cert.patch")
        self.set_marker("patched")


recipe = MaterialYouColorRecipe()
