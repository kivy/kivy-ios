# pure-python package, this can be removed when we'll support any python package
from toolchain import PythonRecipe


class PlyerRecipe(PythonRecipe):
    version = "2.2.0"
    url = "https://pypi.python.org/packages/71/2a/2e4e77803a8bd6408a2903340ac498cb0a2181811af7c9ec92cb70b0308a/Pygments-2.2.0.tar.gz"
    depends = ["python"]
    archs = ["i386"]

recipe = PlyerRecipe()
