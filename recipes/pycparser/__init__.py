from toolchain import PythonRecipe


class PycparserRecipe(PythonRecipe):
    name = "pycparser"
    version = "2.14"
    url = (
        "https://pypi.python.org/packages/6d/31/"
        "666614af3db0acf377876d48688c5d334b6e493b96d21aa7d332169bee50/"
        "pycparser-{version}.tar.gz"
    )
    depends = ["python"]

recipe = PycparserRecipe()
