from kivy_ios.toolchain import PythonRecipe


class BitarrayRecipe(PythonRecipe):
    version = "3.0.0"
    url = "https://github.com/ilanschnell/bitarray/archive/refs/tags/{version}.tar.gz"
    depends = ["hostpython3", "python3"]


recipe = BitarrayRecipe()