# -*- coding: utf-8 -*-
from toolchain import Recipe
import logging

logger = logging.getLogger(__name__)


class HostpythonAliasRecipe(Recipe):
    is_alias = True

    def init_after_import(self, ctx):
        # The hostpython version was previously determined via
        #     hostpython = ctx.state.get("hostpython")
        hostpython = "hostpython3"
        self.depends = [hostpython]


recipe = HostpythonAliasRecipe()
