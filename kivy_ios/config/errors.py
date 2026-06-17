"""Configuration validation errors.

Kept free of any CLI/click dependency so the config layer is importable and
testable in isolation. The CLI converts ``ConfigError`` into a clean
user-facing message.
"""

from __future__ import annotations


class ConfigError(Exception):
    """A semantic or structural problem in ``pyproject.toml``.

    Carries an optional ``key_path`` (dotted TOML location, e.g.
    ``tool.kivy.ios.bundle_id``) and a best-effort ``line`` number so the CLI
    can point the user at the offending spot with a remediation ``hint``.
    """

    def __init__(
        self,
        message: str,
        *,
        key_path: str | None = None,
        line: int | None = None,
        hint: str | None = None,
    ) -> None:
        self.message = message
        self.key_path = key_path
        self.line = line
        self.hint = hint
        super().__init__(message)

    def format(self) -> str:
        parts = []
        location = ""
        if self.line is not None:
            location = f" (line {self.line})"
        elif self.key_path is not None:
            location = f" ([{self.key_path}])"
        parts.append(f"{self.message}{location}")
        if self.hint:
            parts.append(f"  hint: {self.hint}")
        return "\n".join(parts)
