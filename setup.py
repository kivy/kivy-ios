import os
from glob import glob
from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


def recursive_include(module):
    module_path = module.replace(".", "/") + "/"
    files = glob(f"{module_path}**", recursive=True)
    return [file.replace(module_path, "") for file in files]


setup(
    name="kivy-ios",
    version="1.3.0.dev0",
    description="Kivy for iOS",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="The Kivy team",
    author_email="kivy-dev@googlegroups.com",
    url="https://github.com/kivy/kivy-ios",
    python_requires=">=3.6.0",
    install_requires=["cookiecutter", "pbxproj", "Pillow", "requests", "sh"],
    packages=find_packages(),
    package_data={
        # note this method is a bit excessive as it includes absolutely everything
        # make sure you run with from a clean directory
        "kivy_ios": recursive_include("kivy_ios"),
    },
    entry_points={"console_scripts": ["toolchain = kivy_ios.toolchain:main"]},
)
