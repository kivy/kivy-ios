# -*- coding: utf-8 -*-
import sys
from toolchain import Recipe
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
            elif "python3" in ctx.wanted_recipes:
                python = "python3"
            else:
                logger.error("No Python version set in the build.")
                logger.error("Add python2 or python3 in your recipes:")
                logger.error("./toolchain.py build python3 ...")
                sys.exit(1)
        if python:
            self.depends = [python]
        self.recipe_dir = join(ctx.root_dir, "recipes", python)

recipe = PythonAliasRecipe()
