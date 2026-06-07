from __future__ import annotations

import json

from asc_rcm_lite.journeys import execute_vp_revenue_cycle_journey


def main() -> int:
    print(json.dumps(execute_vp_revenue_cycle_journey().to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
