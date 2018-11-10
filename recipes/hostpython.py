# -*- coding: utf-8 -*-
import sys
from toolchain import Recipe

class HostpythonAliasRecipe(Recipe):
    is_alias = True

    def init_after_import(self, ctx):
        hostpython = ctx.state.get("hostpython")
        if not hostpython:
            # search in wanted_recipes if it's the first time
            if "hostpython2" in ctx.wanted_recipes:
                hostpython = "hostpython2"
            elif "hostpython3" in ctx.wanted_recipes:
                hostpython = "hostpython3"
            else:
                print("")
                print("ERROR: No hostpython version set in the build.")
                print("ERROR: Add python2 or python3 in your recipes:")
                print("ERROR: ./toolchain.py build python3 ...")
                print("")
                sys.exit(1)
        if hostpython:
            self.depends = [hostpython]

recipe = HostpythonAliasRecipe()
