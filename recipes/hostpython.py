# -*- coding: utf-8 -*-
from toolchain import Recipe

class HostpythonAliasRecipe(Recipe):
    is_alias = True

    def init_after_import(self, ctx):
        hostpython = ctx.state.get("hostpython")
        if not hostpython:
            print("WARNING: no hostpython set yet, so you need to specify")
            print("WARNING: either hostpython2 or hostpython3 in your deps")
        else:
            self.depends = [hostpython]

recipe = HostpythonAliasRecipe()
