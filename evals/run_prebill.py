from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.evals.metrics import run_prebill_eval


def run_prebill() -> dict:
    return run_prebill_eval()


if __name__ == "__main__":
    print(json.dumps(run_prebill(), indent=2, sort_keys=True))
