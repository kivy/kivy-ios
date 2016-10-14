from toolchain import PythonRecipe


class AutobahnRecipe(PythonRecipe):
    name = "autobahn"
    version = "0.16.0"
    url = "https://github.com/crossbario/autobahn-python/archive/v{version}.zip"
    depends = ["twisted", "six", "txaio"]

recipe = AutobahnRecipe()
