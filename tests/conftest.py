from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_fixture(name: str) -> dict[str, Any]:
    fixture = Path(__file__).parent / "fixtures" / name
    data = json.loads(fixture.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data
