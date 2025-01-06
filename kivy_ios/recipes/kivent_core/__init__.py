"""
Author: Lawrence Du
E-mail: larrydu88@gmail.com
"""

from kivy_ios.toolchain import CythonRecipe, shprint
import sh
from os.path import join
from os import chdir
import logging

logger = logging.getLogger(__name__)


class KiventCoreRecipe(CythonRecipe):
    version = 'master'
    url = 'https://github.com/kivy/kivent/archive/{version}.zip'
    name = 'kivent_core'
    depends = ['libffi', 'kivy']  # note: unsure if libffi is necessary here
    pre_build_ext = False
    subbuilddir = False
    cythonize = True
    pbx_frameworks = ["OpenGLES"]  # note: This line may be unnecessary
    hostpython_prerequisites = ["Cython==0.29.37"]

    def get_recipe_env(self, plat):
        env = super(KiventCoreRecipe, self).get_recipe_env(plat)
        env['CYTHONPATH'] = self.get_recipe(
            'kivy', self.ctx).get_build_dir(plat)
        return env

    def get_build_dir(self, plat, sub=False):
        """
        Call this to get the correct build_dir, where setup.py is located which is
        actually under modules/core/setup.py
        """
        builddir = super(KiventCoreRecipe, self).get_build_dir(plat)
        if sub or self.subbuilddir:
            core_build_dir = join(builddir, 'modules', 'core')
            logger.info("Core build directory is located at {}".format(core_build_dir))
            return core_build_dir
        else:
            logger.info("Building in {}".format(builddir))
            return builddir

    def build_platform(self, plat):
        """
        Override build.arch to avoid calling setup.py here (Call it in
        install() instead).
        """
        self.subbuildir = True
        self.cythonize_build()
        self.biglink()
        self.subbuilddir = False

    def install(self):
        """
        This method simply builds the command line call for calling
        kivent_core/modules/core/setup.py

        This constructs the equivalent of the command
        "$python setup.py build_ext install"
        only with the environment variables altered for each different architecture
        The appropriate version of kivy also needs to be added to the path, and this
        differs for each architecture (i386, x86_64, armv7, etc)

        Note: This method is called by build_all() in toolchain.py

        """
        plat = list(self.platforms_to_build)[0]

        build_dir = self.get_build_dir(plat, sub=True)
        logger.info("Building kivent_core {} in {}".format(plat.arch, build_dir))
        chdir(build_dir)
        hostpython = sh.Command(self.ctx.hostpython)

        # Get the appropriate environment for this recipe (including CYTHONPATH)
        # build_env = plat.get_env()
        build_env = self.get_recipe_env(plat)

        dest_dir = join(self.ctx.dist_dir, "root", "python")
        build_env['PYTHONPATH'] = join(dest_dir, 'lib', 'python3.7', 'site-packages')

        # Add Architecture specific kivy path for 'import kivy' to PYTHONPATH
        arch_kivy_path = self.get_recipe('kivy', self.ctx).get_build_dir(plat)
        build_env['PYTHONPATH'] = join(build_env['PYTHONPATH'], ':', arch_kivy_path)

        # Make sure you call kivent_core/modules/core/setup.py
        subdir_path = self.get_build_dir(plat, sub=True)
        setup_path = join(subdir_path, "setup.py")

        # Print out directories for sanity check
        logger.info("ENVS", build_env)
        logger.info("ROOT", self.ctx.root_dir)
        logger.info("BUILD", self.ctx.build_dir)
        logger.info("INCLUDE", self.ctx.include_dir)
        logger.info("DISTDIR", self.ctx.dist_dir)
        logger.info("ARCH KIVY LOC", self.get_recipe('kivy', self.ctx).get_build_dir(plat))

        shprint(hostpython, setup_path, "build_ext", "install", _env=build_env)


recipe = KiventCoreRecipe()
