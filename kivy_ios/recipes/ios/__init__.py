from kivy_ios.toolchain import CythonRecipe


class IosRecipe(CythonRecipe):
    version = "master"
    url = "src"
    library = "libios.a"
    depends = ["python"]
    pbx_frameworks = ["MessageUI", "CoreMotion", "UIKit", "WebKit", "Photos"]
    hostpython_prerequisites = ["Cython==0.29.37"]

    def install(self):
        self.install_python_package(
            name=self.so_filename("ios"), is_dir=False)


recipe = IosRecipe()
