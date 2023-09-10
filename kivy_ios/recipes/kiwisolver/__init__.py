'''
This file is derived from the p4a recipe for kiwisolver.
It is a dependency of matplotlib.

It is a C++ library, and it utilizes the cpplink script to handle
creating the library files needed for inclusion in an iOS project.

It also depends on the headers from the cppy package.
'''

from kivy_ios.toolchain import CythonRecipe
from os.path import join


class KiwiSolverRecipe(CythonRecipe):

    site_packages_name = 'kiwisolver'
    version = '1.3.2'
    url = 'https://github.com/nucleic/kiwi/archive/{version}.zip'
    depends = ["python"]
    hostpython_prerequisites = ["cppy"]
    cythonize = False
    library = "libkiwisolver.a"

    def get_recipe_env(self, plat):
        env = super().get_recipe_env(plat)

        # cpplink setup
        env['CXX_ORIG'] = env['CXX']
        env['CXX'] = join(self.ctx.root_dir, "tools", "cpplink")

        # setuptools uses CC for compiling and CXX for linking
        env['CC'] = env['CXX']
        env['CFLAGS'] += ' -isysroot {}'.format(env['IOSSDKROOT'])
        return env


recipe = KiwiSolverRecipe()
