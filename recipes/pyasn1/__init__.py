from toolchain import PythonRecipe


class Pyasn1Recipe(PythonRecipe):
    name = "pyasn1"
    version = "0.1.9"
    url = (
        "https://pypi.python.org/packages/f7/83/"
        "377e3dd2e95f9020dbd0dfd3c47aaa7deebe3c68d3857a4e51917146ae8b/"
        "pyasn1-{version}.tar.gz"
    )
    depends = ["python"]

recipe = Pyasn1Recipe()
