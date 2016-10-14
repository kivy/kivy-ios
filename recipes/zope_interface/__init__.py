from toolchain import CythonRecipe


class ZopeInterfaceRecipe(CythonRecipe):
    name = "zope"
    version = "4.3.2"
    url = "https://github.com/zopefoundation/zope.interface/archive/{version}.zip"
    depends = ["python", "host_setuptools"]
    cythonize = False


recipe = ZopeInterfaceRecipe()
