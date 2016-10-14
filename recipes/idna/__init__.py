from toolchain import PythonRecipe


class IdnaRecipe(PythonRecipe):
    name = "idna"
    version = "2.1"
    url = (
        "https://pypi.python.org/packages/fb/84/"
        "8c27516fbaa8147acd2e431086b473c453c428e24e8fb99a1d89ce381851/"
        "idna-{version}.tar.gz"
    )
    depends = ["python"]

recipe = IdnaRecipe()
