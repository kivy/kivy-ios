import sh
import shutil
import subprocess

def modified_recipes(branch='origin/master'):
    """
    Returns a set of modified recipes between the current branch and the one
    in param.
    """
    # using the contrib version on purpose rather than sh.git, since it comes
    # with a bunch of fixes, e.g. disabled TTY, see:
    # https://stackoverflow.com/a/20128598/185510
    sh.contrib.git.fetch("origin", "master")
    git_diff = sh.contrib.git.diff('--name-only', branch)
    recipes = set()
    for file_path in git_diff:
        if 'recipes/' in file_path:
            recipe = file_path.split('/')[1]
            recipes.add(recipe)
    return recipes

if __name__ == "__main__":
    updated_recipes = " ".join(modified_recipes())
    if updated_recipes != '':
        subprocess.run(f"python3 toolchain.py build {updated_recipes}", shell=True, check=True)
    else:
        print("Nothing to do. No updated recipes.")