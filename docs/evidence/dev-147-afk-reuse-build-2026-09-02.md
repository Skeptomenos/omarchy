# DEV-147 AFK reuse offline build

**Date:** 2026-09-02
**Scope:** Exact AppleDRM build and non-default candidate image

## Inputs

The source is Asahi commit `e2e1930a9595bffafad92cec2b5504525efb9cd4`. The five-file patch has SHA-256 `9b52faf901123ab4f9a0a486c2f7ba5718259dcb0ef68e4aebc9ce3d23a19e2c`. Both builds use the same retained `7.1.6-1-1-ARCH` headers, `Module.symvers`, tool manifest, virtual source path, and offline sandbox.

The sandbox has no network, `/proc`, `/sys`, `/boot`, `/home`, or live module access. It runs as UID and GID 1001. Its input fingerprints remained unchanged.

## Module result

The control run is `run-zh898jzw`. Its module has SHA-256 `c8fffa9a663760cb3c2f66f8d9123c76f01a6a5dfc51744ece1d36af1e54f7c3`. It is byte-identical to the earlier independent control build.

The candidate run is `run-e1u1_2m7`. Its module has SHA-256 `d6332afdf58f4af403201b7a6a469e1202f4370972f85a00054ecd563717d649` and build ID `1ca52ad1cea00559d5fdfd32177e4d1e694994e1`.

The candidate keeps the stock module name, vermagic, dependencies, aliases, and empty export set. Its only new kernel imports are `_raw_spin_lock` and `_raw_spin_unlock`. Both are exported by the pinned kernel. No import was removed. The module is an AArch64 ELF64 relocatable. DWARF, BTF, and `.BTF.base` are present and readable. Build stderr is empty. Independent QA and review report PASS.

## Image result

The image builder uses the accepted 19,184,210-byte image with SHA-256 `a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196` as its base. A control-module negative run exits 1 and publishes no image.

The candidate run is `run-935pw0qu`. It changes exactly this member:

```text
usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/gpu/drm/apple/appledrm.ko
```

The early archive and the other 1,161 main records remain byte-identical. The generated image is 21,598,988 bytes with SHA-256 `ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd`. Exact decompression, archive parsing, module metadata, build ID, exclusive mode-0600 publication, and full readback pass. Independent review reports PASS.

The image is not staged, loaded, or booted. The accepted image, normal image, active `boot.bin`, packages, live modules, and running kernel remain unchanged.
