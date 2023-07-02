from kivy_ios.toolchain import PythonRecipe


class PykkaRecipe(PythonRecipe):
    version = '1.2.1'
    url = 'https://github.com/jodal/pykka/archive/v{version}.zip'

    depends = ['python3']

    site_packages_name = 'pykka'


recipe = PykkaRecipe()
