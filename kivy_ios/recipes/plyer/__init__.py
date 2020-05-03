from kivy_ios.toolchain import PythonRecipe


class PlyerRecipe(PythonRecipe):
    version = "master"
    url = "https://github.com/kivy/plyer/archive/{version}.zip"
    depends = ["python", "pyobjus"]
    archs = ["x86_64"]


recipe = PlyerRecipe()
