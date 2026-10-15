#!/usr/bin/env python3
"""Refresh or check the BCR overlay integrity map."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
version = root / "modules/e2fsprogs/1.47.4"
overlay = version / "overlay"
# Keep the BCR test module identical to the checkout's validation workspace.
for relative in ["MODULE.bazel", "BUILD.bazel", "platforms.bzl", "tests/filesystem_test.sh"]:
    destination = overlay / "test_module" / relative
    content = (root / relative).read_bytes()
    if args.check:
        if not destination.exists() or destination.read_bytes() != content:
            raise SystemExit(f"BCR test module is stale: {relative}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
source_path = version / "source.json"
source = json.loads(source_path.read_text())
source["overlay"] = {
    path.relative_to(overlay).as_posix(): "sha256-"
    + base64.b64encode(hashlib.sha256(path.read_bytes()).digest()).decode()
    for path in sorted(overlay.rglob("*"))
    if path.is_file() and not path.is_symlink() and path.name != "MODULE.bazel.lock"
}
expected = json.dumps(source, indent=4) + "\n"
module = (overlay / "MODULE.bazel").read_text()
if args.check:
    if source_path.read_text() != expected:
        raise SystemExit("Overlay checksums are stale; run tools/update_integrity.py")
    if (version / "MODULE.bazel").read_text() != module:
        raise SystemExit("Registry and overlay MODULE.bazel differ")
    print("Registry module and overlay checksums match")
else:
    source_path.write_text(expected)
    (version / "MODULE.bazel").write_text(module)
