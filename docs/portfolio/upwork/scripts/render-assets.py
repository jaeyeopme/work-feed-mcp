from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
OUTPUT = ROOT / "outputs"

ASSETS = [
    "mcp-tool-integration-flow",
    "mcp-safety-boundary",
]


def render(name: str) -> None:
    html = SOURCE / f"{name}.html"
    png = OUTPUT / f"{name}.png"
    subprocess.run(
        [
            "playwright",
            "screenshot",
            "--viewport-size=1600,900",
            f"file://{html}",
            str(png),
        ],
        check=True,
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS:
        render(asset)


if __name__ == "__main__":
    main()
