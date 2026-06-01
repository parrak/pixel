from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.run_charges import run_charges
from evals.run_coding import run_coding
from evals.run_denials import run_denials
from evals.run_prebill import run_prebill
from evals.run_um import run_um


def run_all() -> dict:
    return {
        "prebill": run_prebill(),
        "coding": run_coding(),
        "denials": run_denials(),
        "charges": run_charges(),
        "utilization": run_um(),
    }


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2, sort_keys=True))
