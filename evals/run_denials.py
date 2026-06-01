from __future__ import annotations

import json


def run_denials() -> dict:
    return {"status": "not_implemented", "cases": 0}


if __name__ == "__main__":
    print(json.dumps(run_denials(), indent=2, sort_keys=True))

