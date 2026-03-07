from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def _load_evaluate_release_readiness():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.release_audit import evaluate_release_readiness

    return evaluate_release_readiness


def main() -> None:
    evaluate_release_readiness = _load_evaluate_release_readiness()
    payload = evaluate_release_readiness(ROOT)
    print(json.dumps(payload, indent=2))
    if payload["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
