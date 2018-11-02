# -*- coding: utf-8 -*-
from toolchain import Recipe

class PythonAliasRecipe(Recipe):
    is_alias = True

    def init_after_import(self, ctx):
        python = ctx.state.get("python")
        if not python:
            print("WARNING: no python set yet, so you need to specify")
            print("WARNING: either python2 or python3 in your deps")
        else:
            self.depends = [python]

recipe = PythonAliasRecipe()
