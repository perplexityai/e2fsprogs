load("@with_cfg.bzl", "with_cfg")

linux_amd64_files, _linux_amd64_files = with_cfg(native.filegroup).set("platforms", [Label("@llvm//platforms:linux_x86_64")]).set("compilation_mode", "opt").build()
linux_arm64_files, _linux_arm64_files = with_cfg(native.filegroup).set("platforms", [Label("@llvm//platforms:linux_aarch64")]).set("compilation_mode", "opt").build()
