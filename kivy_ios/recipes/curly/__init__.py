from kivy_ios.toolchain import CythonRecipe


class CurlyRecipe(CythonRecipe):
    version = "master"
    url = "https://github.com/tito/curly/archive/{version}.zip"
    library = "libcurly.a"
    depends = ["python", "libcurl", "sdl2", "sdl2_image"]
    pre_build_ext = True
    hostpython_prerequisites = ["Cython==0.29.37"]


recipe = CurlyRecipe()
