# -*- coding: utf-8 -*-
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
                print("WARNING: no hostpython set yet, so you need to specify")
                print("WARNING: either hostpython2 or hostpython3 in your deps")
        if python:
            self.depends = [hostpython]

recipe = HostpythonAliasRecipe()
