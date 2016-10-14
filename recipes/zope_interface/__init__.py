from toolchain import CythonRecipe, shprint
from os.path import join
import sh


class ZopeInterfaceRecipe(CythonRecipe):
    version = "4.3.2"
    url = "https://github.com/zopefoundation/zope.interface/archive/{version}.zip"
    #library = "libzopeinterface.a"
    depends = ["python", "host_setuptools"]
    cythonize = False

    def get_recipe_env(self, arch):
        env = super(ZopeInterfaceRecipe, self).get_recipe_env(arch)
        #env["CC"] = "{} {}".format(env["CC"], env["CFLAGS"])
        return env

    def build_arch(self, arch):
        super(ZopeInterfaceRecipe, self).build_arch(arch)


recipe = ZopeInterfaceRecipe()
