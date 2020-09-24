# -*- coding: utf-8 -*-
import sys
from kivy_ios.toolchain import Recipe
import logging

logger = logging.getLogger(__name__)


class HostpythonAliasRecipe(Recipe):
    """
    Note this recipe was created to handle both hostpython2 and hostpython3.
    As hostpython2 support was dropped, this could probably be simplified.
    """
    is_alias = True

    def init_after_import(self, ctx):
        hostpython = ctx.state.get("hostpython")
        if not hostpython:
            # search in wanted_recipes if it's the first time
            if "hostpython3" in ctx.wanted_recipes:
                hostpython = "hostpython3"
            else:
                logger.error("No hostpython version set in the build.")
                logger.error("Add python3 in your recipes:")
                logger.error("./toolchain.py build python3 ...")
                sys.exit(1)
        if hostpython:
            self.depends = [hostpython]


recipe = HostpythonAliasRecipe()
