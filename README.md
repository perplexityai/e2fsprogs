# e2fsprogs Bazel overlay

Native Bazel builds of e2fsprogs 1.47.4 for SPACE worker images. This repository
is a BCR-format registry overlay, fetching the checksum-pinned upstream release.
It is not yet published in Bazel Central Registry.

All C compilation and linking use `cc_library` and `cc_binary`. The validation
workspace pins [hermeticbuild/hermetic-llvm](https://github.com/hermeticbuild/hermetic-llvm)
through BCR's `llvm@0.8.21` and registers `@llvm//toolchain:all`.
`with_cfg.bzl` transitions the complete tool dependency graph to optimized Linux
x86_64 and aarch64 configurations. The CRC table generator runs in the execution
configuration, including during cross-compilation. Configure and Make are not
invoked by the build.

## Build and validate

With Bazel 9.2.0, from this checkout:

```sh
python3 tools/update_integrity.py --check
bazel build --registry="file://$PWD" --registry=https://bcr.bazel.build \
  //:linux_amd64 //:linux_arm64
bazel test --registry="file://$PWD" --registry=https://bcr.bazel.build \
  --test_output=errors //:filesystem_test
```

The filesystem test runs on the host architecture and uses a native Bazel-built,
test-only `mke2fs` fixture. It creates a journaled ext4 image with metadata checksums
and 64-bit block numbers, sets and verifies its label, grows and shrinks it,
verifies each block count, and runs read-only `e2fsck` after every change.
It needs no privileges, mounts, loop devices, or host e2fsprogs installation.
Cross-built binaries are build outputs; the test does not emulate aarch64.

## Consume the overlay

Add this registry before BCR with `--registry=file:///absolute/path/to/e2fsprogs`
(or serve its contents at an immutable HTTP URL), and add to `MODULE.bazel`:

```starlark
bazel_dep(name = "e2fsprogs", version = "1.47.4")
bazel_dep(name = "llvm", version = "0.8.21")
register_toolchains("@llvm//toolchain:all")
```

Public executable targets are `@e2fsprogs//:e2fsck`, `:resize2fs`, `:dumpe2fs`,
and `:tune2fs`. They follow the consumer's target platform. The libraries
`:ext2fs`, `:e2p`, `:com_err`, `:uuid`, `:blkid`, and `:support` are native Bazel
libraries. Filesystem libraries are linked into the tools; they do not require
system copies of libext2fs, libe2p, libcom_err, libuuid, or libblkid.

The root `//:linux_amd64` and `//:linux_arm64` targets demonstrate `with_cfg`
platform transitions and expose the four executable files for OCI packaging.
The overlay leaves compiler selection to its consumer, while this validation
workspace registers hermetic LLVM explicitly. No changes to SPACE are included.

## Platform contract

Configuration headers describe little-endian Linux LP64 with glibc, matching
hermetic LLVM's Linux x86_64/aarch64 platforms (glibc 2.28 baseline). Other OS/CPU
combinations are incompatible. musl, 32-bit, and big-endian targets are unsupported.
Native-language message catalogs, external libarchive, libmagic, and uuidd are
disabled. MMP, TDB undo I/O, quota support, and journal recovery remain enabled.
Runtime configuration files still use `/etc`; packaging those belongs to consumers.

## Maintain

`modules/e2fsprogs/1.47.4/source.json` pins the release archive and each overlay
file. After editing the overlay, run `python3 tools/update_integrity.py` and check
in both the overlay and integrity changes. `MODULE.bazel` beside `source.json`
must match its overlaid copy; the updater synchronizes them.

`lib/config.h` is an explicit platform configuration, not a host probe.
The LP64 type headers are substituted from upstream `.h.in` templates with
8/16/32/64-bit integer types, 64-bit long/pointers/off_t/time_t, and little endian.
`uuid.h` and `blkid.h` are unchanged copies of the upstream templates.
`ext2_err.c/.h` and `prof_err.c/.h` retain upstream generator notices and are
release-specific outputs of `lib/et/et_c.awk` and `et_h.awk`; substitute
`@E2FSPROGS_VERSION@` with `1.47.4` in `ext2_err.et.in` first. Generate using
`outfile=<output path>` and `outfn=<basename>` to keep paths out of the outputs.
`misc/default_profile.c` is the output of upstream `misc/profile-to-c.awk` on
`misc/mke2fs.conf.in` and is used only by the test formatter.
These fixed outputs avoid host AWK/configure dependencies in Bazel actions.
The CRC table is generated during the build by its native C executable.

During overlay development, an extracted upstream tree with the overlay copied
on top can be used with `--override_repository=e2fsprogs=/path/to/tree`. Validate
through a fresh registry location afterward: released registry metadata is
immutable and Bazel may retain it during a server session.

The registry metadata intentionally has no enrolled BCR maintainers. Enroll
maintainers and confirm the BCR submission's presubmit matrix before proposing
this module to the public registry. Upstream license terms are in `NOTICE` and
individual source files.

The registry presubmit uses `overlay/test_module`, synchronized from this root
validation workspace by the integrity updater. Its cross-builds and filesystem
test use the same pinned LLVM toolchain.
