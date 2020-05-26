BROKEN_RECIPES = set(
    [
        # bad install directory or PYTHONPATH
        # https://github.com/kivy/kivy-ios/issues/468
        "werkzeug",
    ]
)

# recipes that were already built will be skipped
CORE_RECIPES = set(["kivy", "hostpython3", "python3"])
