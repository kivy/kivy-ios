from toolchain import PythonRecipe


class PyOpenSSLRecipe(PythonRecipe):
    name = "OpenSSL"
    version = "16.1.0"
    url = (
        "https://pypi.python.org/packages/15/1e/"
        "79c75db50e57350a7cefb70b110255757e9abd380a50ebdc0cfd853b7450/"
        "pyOpenSSL-{version}.tar.gz"
    )
    depends = ["openssl", "six", "cryptography"]

recipe = PyOpenSSLRecipe()
