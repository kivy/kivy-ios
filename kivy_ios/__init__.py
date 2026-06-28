"""kivy-ios: a declarative iOS bundler for Kivy apps.

kivy-ios 3.0 reads a user-authored ``pyproject.toml`` (PEP 621 ``[project]``
plus ``[tool.kivy]`` / ``[tool.kivy.ios]``), resolves a PEP 751
``pylock.ios.toml`` build manifest, and materializes it into a generated
Xcode project. See ``docs/proposals`` for the full specification.
"""

__version__ = "3.0.0.dev0"
