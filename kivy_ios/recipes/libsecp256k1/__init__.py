from kivy_ios.toolchain import Recipe, shprint
from os.path import join, exists
from multiprocessing import cpu_count
import sh

class LibSecp256k1Recipe(Recipe):
    version = 'b0452e6'
    url = 'https://github.com/bitcoin-core/secp256k1/archive/{version}.zip'
    library = '.libs/libsecp256k1.a'
    include_per_arch = True

    def build_arch(self, arch):
        super(LibSecp256k1Recipe, self).build_arch(arch)
        env = self.get_recipe_env(arch)
                
        if not exists(join(self.build_dir, "configure")):
            shprint(sh.Command('./autogen.sh'))
        shprint(
            sh.Command('./configure'),
            '--host=' + arch.triple,
            '--prefix=/',
            '--enable-module-recovery',
            '--enable-experimental',
            '--enable-module-ecdh',
            '--disable-shared',
            _env=env)
        shprint(sh.make, '-j' + str(cpu_count()), _env=env)

recipe = LibSecp256k1Recipe()
