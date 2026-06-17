"""Check result types for doctor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


# Severity ordering for computing the overall worst status.
_ORDER = {Status.PASS: 0, Status.SKIP: 0, Status.WARN: 1, Status.FAIL: 2}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: Status
    detail: str = ""
    hint: str = ""

    def render(self) -> str:
        line = f"[{self.status.value}] {self.name}"
        if self.detail:
            line += f": {self.detail}"
        if self.hint and self.status in (Status.WARN, Status.FAIL):
            line += f"\n       hint: {self.hint}"
        return line


def worst_status(results: list[CheckResult]) -> Status:
    worst = Status.PASS
    for r in results:
        if _ORDER[r.status] > _ORDER[worst]:
            worst = r.status
    return worst
