'''
This file is derived from the p4a recipe for kiwisolver.
It is a dependency of matplotlib.

It also depends on the headers from the cppy package.
'''

from kivy_ios.toolchain import CythonRecipe


class KiwiSolverRecipe(CythonRecipe):

    site_packages_name = 'kiwisolver'
    version = '1.3.2'
    url = 'https://github.com/nucleic/kiwi/archive/{version}.zip'
    depends = ["python"]
    hostpython_prerequisites = ["cppy", "Cython==0.29.37"]
    cythonize = False
    library = "libkiwisolver.a"


recipe = KiwiSolverRecipe()
