# -*- coding: utf-8 -*-
import sys
from toolchain import Recipe
import logging
from os.path import join

logger = logging.getLogger(__name__)


class PythonAliasRecipe(Recipe):
    is_alias = True

    def init_after_import(self, ctx):
        # The python version was previously deteremind via
        #     python = ctx.state.get("python")
        python = "python3"
        self.depends = [python]
        self.recipe_dir = join(ctx.root_dir, "recipes", python)


recipe = PythonAliasRecipe()
