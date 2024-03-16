#!/usr/bin/env python
"""
Continuous Integration helper script.
Automatically detects recipes modified in a changeset (compares with master)
and recompiles them.

Current limitations:
- will fail on conflicting requirements
"""
import sh
import subprocess
from fnmatch import fnmatch
from constants import CORE_RECIPES, BROKEN_RECIPES


def modified_recipes(branch="origin/master"):
    """
    Returns a set of modified recipes between the current branch and the one
    in param.
    """
    # using the contrib version on purpose rather than sh.git, since it comes
    # with a bunch of fixes, e.g. disabled TTY, see:
    # https://stackoverflow.com/a/20128598/185510
    sh.contrib.git.fetch("origin", "master")
    git_diff = sh.contrib.git.diff("--name-only", "--diff-filter=d", branch).split("\n")
    recipes = set()
    for file_path in git_diff:
        if fnmatch(file_path, "kivy_ios/recipes/*/__init__.py"):
            recipe = file_path.split("/")[2]
            recipes.add(recipe)
    return recipes


def main():
    recipes = modified_recipes()
    recipes -= CORE_RECIPES
    recipes -= BROKEN_RECIPES
    updated_recipes = " ".join(recipes)
    if updated_recipes != "":
        subprocess.run(
            f"toolchain build {updated_recipes}", shell=True, check=True
        )
    else:
        print("Nothing to do. No updated recipes.")


if __name__ == "__main__":
    main()
