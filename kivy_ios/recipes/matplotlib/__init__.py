'''
This file is derived from the p4a recipe for matplotlib.
It is a dependency of matplotlib.

In addition to the original patch files for p4a, additional patch files
are necessary to prevent duplicate symbols from appearing in the final
link of a kivy-ios application.
'''

from kivy_ios.toolchain import CythonRecipe, ensure_dir
from os.path import join, abspath, dirname
import shutil
import sh


class MatplotlibRecipe(CythonRecipe):
    version = '3.7.2'
    url = 'https://github.com/matplotlib/matplotlib/archive/v{version}.zip'
    library = 'libmatplotlib.a'
    depends = ['kiwisolver', 'numpy', 'pillow', 'freetype']
    pre_build_ext = True
    python_depends = ['cycler', 'fonttools', 'packaging',
                      'pyparsing', 'python-dateutil', 'six']
    hostpython_prerequisites = ['pybind11', 'certifi', "Cython==0.29.37"]
    cythonize = False

    def generate_libraries_pc_files(self, plat):
        """
        Create *.pc files for libraries that `matplotib` depends on.

        Because, for unix platforms, the mpl install script uses `pkg-config`
        to detect libraries installed in non standard locations (our case...
        well...we don't even install the libraries...so we must trick a little
        the mlp install).
        """
        pkg_config_path = self.get_recipe_env(plat)['PKG_CONFIG_PATH']
        ensure_dir(pkg_config_path)

        lib_to_pc_file = {
            # `pkg-config` search for version freetype2.pc, our current
            # version for freetype, but we have our recipe named without
            # the version...so we add it in here for our pc file
            'freetype': 'freetype2.pc',
        }

        for lib_name in {'freetype'}:
            pc_template_file = join(
                abspath(self.recipe_dir),
                f'lib{lib_name}.pc.template'
            )
            # read template file into buffer
            with open(pc_template_file) as template_file:
                text_buffer = template_file.read()
            # set the library absolute path and library version
            lib_recipe = self.get_recipe(lib_name, self.ctx)
            text_buffer = text_buffer.replace(
                'path_to_built', lib_recipe.get_build_dir(plat),
            )
            text_buffer = text_buffer.replace(
                'library_version', lib_recipe.version,
            )

            # write the library pc file into our defined dir `PKG_CONFIG_PATH`
            pc_dest_file = join(pkg_config_path, lib_to_pc_file[lib_name])
            with open(pc_dest_file, 'w') as pc_file:
                pc_file.write(text_buffer)

    def prebuild_platform(self, plat):
        if self.has_marker("patched"):
            return
        shutil.copyfile(
            join(abspath(self.recipe_dir), "mplsetup.cfg"),
            join(self.get_build_dir(plat), "mplsetup.cfg"),
        )
        self.generate_libraries_pc_files(plat)
        self.apply_patch('_tri.cpp.patch')
        self.apply_patch('_tri.h.patch')
        self.apply_patch('_tri_wrapper.cpp.patch')
        self.apply_patch('setupext.py.patch')
        self.apply_patch('setup.py.patch')
        with open(join(self.get_build_dir(plat), 'lib', 'matplotlib', '_version.py'), 'w') as of:
            v1, v2, v3 = self.version.split('.')
            of.write(f'''
__version__ = version = '{self.version}'
__version_tuple__ = version_tuple = ({v1}, {v2}, {v3})
''')
        self.set_marker("patched")

    def get_recipe_env(self, plat):
        env = super().get_recipe_env(plat)

        # we make use of the same directory than `XDG_CACHE_HOME`, for our
        # custom library pc files, so we have all the install files that we
        # generate at the same place
        env['XDG_CACHE_HOME'] = join(
            self.get_build_dir(plat),
            'p4a_files'
        )
        env['PKG_CONFIG_PATH'] = env['XDG_CACHE_HOME']

        # creating proper *.pc files for our libraries does not seem enough to
        # success with our build (without depending on system development
        # libraries), but if we tell the compiler where to find our libraries
        # and includes, then the install success :)
        freetype = self.get_recipe('freetype', self.ctx)
        free_inc_dir = join(freetype.get_build_dir(plat), 'include')

        numpytype = self.get_recipe('numpy', self.ctx)
        # this numpy include directory is not in the dist directory
        numpy_inc_dir = dirname(sh.glob(numpytype.get_build_dir(plat) + '/**/_numpyconfig.h', recursive=True)[0])

        env['CFLAGS'] += f' -I{free_inc_dir} -I{numpy_inc_dir}'

        return env


recipe = MatplotlibRecipe()
