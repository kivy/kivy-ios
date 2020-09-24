from kivy_ios.toolchain import CythonRecipe


class PhotoRecipe(CythonRecipe):
    version = "master"
    url = "https://github.com/akshayaurora/photolibrary/archive/master.zip"
    library = "libphotolibrary.a"
    depends = ["python"]
    pbx_frameworks = ["UIKit", "Photos", "MobileCoreServices"]

    def install(self):
        self.install_python_package(name="photolibrary.so", is_dir=False)


recipe = PhotoRecipe()
