# pure-python package, this can be removed when we'll support any python package
from toolchain import PythonRecipe


class PlyerRecipe(PythonRecipe):
    version = "master"
    url = "https://github.com/kivy/plyer/archive/{version}.zip"
    depends = ["python", "pyobjus"]
    archs = ["i386"]

recipe = PlyerRecipe()

