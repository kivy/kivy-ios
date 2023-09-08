from kivy_ios.toolchain import CythonRecipe
import os


class PythonPPCommonWrapperRecipe(CythonRecipe):
    version = "{version}"
    package = "python-ppcommon-wrapper"
    asset_name = "python_ppcommon_wrapper-" + version + ".tar.gz"
    url = "libpython_ppcommon_wrapper.tar.gz"
    library = "libpython_ppcommon_wrapper.a"
    depends = ["python"]
    cythonize = False

    def install(self):
        self.install_python_package(name="python_ppcommon_wrapper.so", is_dir=False)


recipe = PythonPPCommonWrapperRecipe()
