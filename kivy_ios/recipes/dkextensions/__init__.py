from kivy_ios.toolchain import CythonRecipe
import os


class DkExtensionsRecipe(CythonRecipe):
    version = "1.5.2"
    package = "dkextensions"
    asset_name = "dkextensions-" + version + ".tar.gz"
    url = "dkextensions.tar.gz"
    library = "libdkextensions.a"
    depends = ["python", "numpy"]
    cythonize = False

    def install(self):
        self.install_python_package(name="dkextensions.so", is_dir=False)


recipe = DkExtensionsRecipe()
