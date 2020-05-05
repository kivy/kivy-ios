# -*- coding: utf-8 -*-
from kivy_ios.toolchain import Recipe
import logging
from os.path import join

logger = logging.getLogger(__name__)


class PythonAliasRecipe(Recipe):
    """
    Note this recipe was created to handle both python2 and python3.
    As python2 support was dropped, this could probably be simplified.
    """
    is_alias = True

    def init_after_import(self, ctx):
        python = ctx.state.get("python")
        if not python:
            python = "python3"
        self.depends = [python]
        self.recipe_dir = join(ctx.root_dir, "recipes", python)


recipe = PythonAliasRecipe()
