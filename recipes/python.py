# -*- coding: utf-8 -*-
import sys
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
                print("")
                print("ERROR: No Python version set in the build.")
                print("ERROR: Add python2 or python3 in your recipes:")
                print("ERROR: ./toolchain.py build python3 ...")
                print("")
                sys.exit(1)
        if python:
            self.depends = [python]

recipe = PythonAliasRecipe()
