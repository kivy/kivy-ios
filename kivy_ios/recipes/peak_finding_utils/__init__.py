from kivy_ios.toolchain import CythonRecipe
import os


class PeakFindingUtilsRecipe(CythonRecipe):
    version = "{version}"
    package = "peak-finding-utils"
    asset_name = "peak_finding_utils-" + version + ".tar.gz"
    url = "peak_finding_utils.tar.gz"
    library = "libpeak_finding_utils.a"
    depends = ["python", "numpy"]
    cythonize = False

    def install(self):
        self.install_python_package(name="peak_finding_utils.so", is_dir=False)


recipe = PeakFindingUtilsRecipe()
