# -*- coding: utf-8 -*-
from toolchain import Recipe

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
                print("WARNING: no python set yet, so you need to specify")
                print("WARNING: either python2 or python3 in your deps")
        if python:
            self.depends = [python]

recipe = PythonAliasRecipe()
