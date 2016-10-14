from toolchain import PythonRecipe


class SixRecipe(PythonRecipe):
    name = "six"
    version = "1.10.0"
    url = (
        "https://pypi.python.org/packages/b3/b2/"
        "238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/"
        "six-{version}.tar.gz"
    )
    depends = ["python"]

recipe = SixRecipe()
