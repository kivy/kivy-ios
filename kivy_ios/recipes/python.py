# -*- coding: utf-8 -*-
from kivy_ios.toolchain import Recipe
import logging
from os.path import join

logger = logging.getLogger(__name__)


class PythonAliasRecipe(Recipe):
    is_alias = True

    def init_after_import(self, ctx):
        python = ctx.state.get("python")
        if not python:
            # search in wanted_recipes if it's the first time
            if "python2" in ctx.wanted_recipes:
                python = "python2"
            else:
                python = "python3"
        self.depends = [python]
        self.recipe_dir = join(ctx.root_dir, "recipes", python)


recipe = PythonAliasRecipe()
