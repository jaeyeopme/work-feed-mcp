"""Shared CLI output helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Protocol


class JsonRecord(Protocol):
    def to_dict(self) -> dict[str, object]: ...


def emit_jsonl(records: Iterable[JsonRecord]) -> int:
    count = 0
    for record in records:
        print(json.dumps(record.to_dict(), ensure_ascii=False, separators=(",", ":")))
        count += 1
    return count
