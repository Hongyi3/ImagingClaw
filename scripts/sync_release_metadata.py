from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def _load_writer():
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from clawimaging.release_manifest import load_release_manifest, write_release_metadata

    return load_release_manifest, write_release_metadata


def main() -> None:
    load_release_manifest, write_release_metadata = _load_writer()
    manifest = load_release_manifest(ROOT / "release" / "v1.0.yaml")
    written_paths = write_release_metadata(ROOT, manifest=manifest)
    print(json.dumps({"written": written_paths}, indent=2))


if __name__ == "__main__":
    main()
