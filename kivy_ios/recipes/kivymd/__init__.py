from kivy_ios.toolchain import PythonRecipe


class KivyMDRecipe(PythonRecipe):
    version = "master"
    url = f"https://github.com/Neizvestnyj/KivyMD/archive/{version}.zip"
    depends = ["python", "kivy", "pillow"]


recipe = KivyMDRecipe()
