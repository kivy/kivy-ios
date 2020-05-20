BROKEN_RECIPES = set(
    [
        # no attribute 'SourceFileLoader'
        # https://github.com/kivy/kivy-ios/issues/466
        "distribute",
        # 'distutils.core' is not a package
        # https://github.com/kivy/kivy-ios/issues/467
        "markupsafe",
        # depends on markupsafe
        # https://github.com/kivy/kivy-ios/issues/466
        "jinja2",
    ]
)

# recipes that were already built will be skipped
CORE_RECIPES = set(["kivy", "hostpython3", "python3"])
