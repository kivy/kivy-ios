from kivy_ios.toolchain import PythonRecipe


class MaterialYouColorRecipe(PythonRecipe):
    version = "2.0.9"
    url = "https://github.com/T-Dynamos/materialyoucolor-python/releases/download/v{version}/materialyoucolor-{version}.tar.gz"
    depends = ["hostpython3", "python3"]


recipe = MaterialYouColorRecipe()
