# pure-python package, this can be removed when we'll support any python package
from toolchain import PythonRecipe


class docutilsRecipe(PythonRecipe):
    version = "0.14"
    url = "https://pypi.python.org/packages/84/f4/5771e41fdf52aabebbadecc9381d11dea0fa34e4759b4071244fa094804c/docutils-0.14.tar.gz"
    depends = ["python"]
    archs = ["i386"]

recipe = docutilsRecipe()
