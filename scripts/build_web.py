"""Regenerate web/data.js from the graph in mcnavigill/data.

    python scripts/build_web.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcnavigill.web import write_data_js  # noqa: E402

if __name__ == "__main__":
    out = write_data_js(Path(__file__).resolve().parent.parent / "web" / "data.js")
    print(f"wrote {out}")
