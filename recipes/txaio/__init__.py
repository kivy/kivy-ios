from toolchain import PythonRecipe


class TxaioRecipe(PythonRecipe):
    name = "txaio"
    version = "2.5.1"
    url = (
        "https://pypi.python.org/packages/45/e1/"
        "f7d88767d65dbfc20d4b4aa0dad657dbbe8ca629ead2bef24da04630a12a/"
        "txaio-{version}.tar.gz"
    )
    depends = ["six"]

recipe = TxaioRecipe()
