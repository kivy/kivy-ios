from toolchain import CythonRecipe


class ZopeInterfaceRecipe(CythonRecipe):
    name = "zope"
    version = "4.3.2"
    url = 'http://pypi.python.org/packages/source/z/zope.interface/zope.interface-{version}.tar.gz'
    depends = ["python", "host_setuptools"]
    cythonize = False


recipe = ZopeInterfaceRecipe()

