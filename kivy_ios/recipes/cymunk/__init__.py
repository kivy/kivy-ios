"""
Author: Lawrence Du, Lukasz Mach
E-mail: larrydu88@gmail.com, maho@pagema.net
"""

from kivy_ios.toolchain import CythonRecipe


class CymunkRecipe(CythonRecipe):
    version = 'master'
    url = 'https://github.com/kivy/cymunk/archive/{version}.zip'
    name = 'cymunk'
    pre_build_ext = True
    library = 'libcymunk.a'
    hostpython_prerequisites = ["Cython==0.29.37"]
    depends = ['python']

    def get_recipe_env(self, arch):
        ret = super(CymunkRecipe, self).get_recipe_env(arch)
        ret['CFLAGS'] += ' -Wno-implicit-function-declaration'
        return ret


recipe = CymunkRecipe()
