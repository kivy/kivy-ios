BROKEN_RECIPES = set(
    [
        # 'distutils.core' is not a package
        # https://github.com/kivy/kivy-ios/issues/467
        "jinja2",
        # bad install directory or PYTHONPATH
        # https://github.com/kivy/kivy-ios/issues/468
        "werkzeug",
    ]
)

# recipes that were already built will be skipped
CORE_RECIPES = set(["kivy", "hostpython3", "python3"])
