from toolchain import PythonRecipe


class PyMoodstocksRecipe(PythonRecipe):
    version = "master"
    url = "https://github.com/tito/pymoodstocks/archive/{version}.zip"
    depends = ["moodstocks", "kivy", "pyobjus"]
    sources = ["src/ios"]
    archs = ["i386"]


recipe = PyMoodstocksRecipe()


