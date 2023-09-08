from kivy_ios.toolchain import CythonRecipe
import os


class RotationRecipe(CythonRecipe):
    version = "{version}"
    package = "rotation"
    asset_name = "rotation-" + version + ".tar.gz"
    url = "rotation.tar.gz"
    library = "librotation.a"
    depends = ["python", "numpy"]
    cythonize = False

    def install(self):
        self.install_python_package(name="peak_finding_utils.so", is_dir=False)


recipe = RotationRecipe()
