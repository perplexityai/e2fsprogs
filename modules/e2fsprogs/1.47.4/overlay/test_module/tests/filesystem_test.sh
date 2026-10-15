#!/usr/bin/env bash
set -euo pipefail
formatter="$PWD/$1"
checker="$PWD/$2"
resizer="$PWD/$3"
dumper="$PWD/$4"
tuner="$PWD/$5"
cd "$TEST_TMPDIR"
export MKE2FS_CONFIG=/dev/null E2FSCK_CONFIG=/dev/null LC_ALL=C
# No mounts, loop devices, root privileges, or host filesystem tools.
"$formatter" -q -t ext4 -F -b 4096 -O extent,has_journal,metadata_csum,64bit image.ext4 8192
"$checker" -fn image.ext4
"$tuner" -L bazel-overlay image.ext4
"$dumper" -h image.ext4 > before.txt
grep -Eq '^Filesystem volume name: +bazel-overlay$' before.txt
grep -Eq '^Block count: +8192$' before.txt
"$resizer" image.ext4 16384
"$checker" -fn image.ext4
"$dumper" -h image.ext4 > grown.txt
grep -Eq '^Block count: +16384$' grown.txt
"$resizer" image.ext4 8192
"$checker" -fn image.ext4
"$dumper" -h image.ext4 > shrunk.txt
grep -Eq '^Block count: +8192$' shrunk.txt
grep -Eq '^Filesystem volume name: +bazel-overlay$' shrunk.txt
