from toolchain import CythonRecipe


class TwistedRecipe(CythonRecipe):
    name = "twisted"
    version = "16.1.1"
    url = "https://github.com/twisted/twisted/archive/twisted-{version}.zip"
    depends = ["pyopenssl", "zope_interface"]
    cythonize = False


recipe = TwistedRecipe()
