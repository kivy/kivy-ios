"""Phase 3 — golden lockfile: exact serialized pylock.ios.toml output."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from kivy_ios.config import load_config_from_text
from kivy_ios.lock import build_lockfile, dumps

GOLDEN = Path(__file__).parent / "data" / "golden_pylock.ios.toml"


def test_golden_lockfile(
    minimal_pyproject, fake_resolver, fake_python_provider, monkeypatch
):
    # Pin toolchain_version so the golden file is stable across releases.
    import kivy_ios.lock.builder as builder

    monkeypatch.setattr(builder, "__version__", "3.0.0")
    cfg = load_config_from_text(minimal_pyproject)
    lock = build_lockfile(
        cfg,
        minimal_pyproject,
        resolver=fake_resolver,
        python_provider=fake_python_provider,
        now=datetime(2026, 5, 27, 0, 0, 0, tzinfo=UTC),
    )
    rendered = dumps(lock)

    if not GOLDEN.exists():  # first run materializes the golden file
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(rendered, encoding="utf-8")

    expected = GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "serialized lockfile drifted from the golden file. If this change is "
        "intentional, delete tests/lock/data/golden_pylock.ios.toml and re-run."
    )
