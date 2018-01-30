from toolchain import CythonRecipe


class IosNotifRecipe(CythonRecipe):
    version = "master"
    url = "src"
    library = "libnotifications.a"
    pbx_frameworks = ["UserNotifications"]
    depends = ["python"]

    def install(self):
        self.install_python_package(name="notifications.so", is_dir=False)


recipe = IosNotifRecipe()


