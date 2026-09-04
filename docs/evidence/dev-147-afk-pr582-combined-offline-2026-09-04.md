# DEV-147 AFK reuse plus PR582 offline candidate

**Date:** 2026-09-04
**Scope:** Exact-source source contract, AppleDRM build, and non-default image
**Result:** PASS; SWE gates, independent QA, and final review accepted the offline candidate

## Reason for the candidate

The AFK-only generation-2 test reached Type-C, DisplayPort, xHCI, DPTX, and
new AFK services. The external display stayed blank. The external DCP then
reported `crashed=1`, and every compositor atomic operation returned `EINVAL`.
The loaded AFK-only candidate did not include the PR582 poweroff-timeout
change. The [generation-2 record](dev-147-afk-reuse-generation2-dcp-crash-2026-09-04.md)
owns that evidence.

This result does not prove which code wrote the crash flag. It makes the
50 ms clear-swap timeout the strongest known writer candidate. The combined
image is the smallest test of that hypothesis.

## Exact source and composition

The accepted source is:

```text
/home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux
e2e1930a9595bffafad92cec2b5504525efb9cd4
```

The combined source applies these patches in order:

1. `dev/apple-dp-altmode/afk-service-reuse/afk-service-reuse.patch`
   with SHA-256
   `9b52faf901123ab4f9a0a486c2f7ba5718259dcb0ef68e4aebc9ce3d23a19e2c`.
2. `dev/apple-dp-altmode/afk-service-reuse-pr582/pr582-timeout.patch`
   with SHA-256
   `dcf1f6c9fa083e47aeb15e284b4e7004cb853902c653e472c3dc73a7eb7eccb1`.

The second patch retains the 50 ms wait and immediate timeout return. It
removes only the timeout-path `dcp->crashed = true` store and adds a warning.
The genuine RTKit crash writer and the atomic crash guard remain unchanged.
The local patch has no added C block comment. Francisco Vargas authored and
tested the PR582 timeout semantics. The original author record remains in
`dev/apple-dp-altmode/pr582/pr582-upstream.patch`.

The source manifest SHA-256 values are:

```text
fca34cbadd373f18a1cad0f32d5e1a94cd0ad0317d665c8ef18733b82e2f41b3  control-source.sha256
ec67d69cc9551d52c65816520dbde37039f0f6d871fd3fbdaeec9a86d984fb9d  combined-source.sha256
```

Only these source files differ:

```text
afk.c
afk.h
epic/dpavservep.c
epic/dpavservep.h
iomfb.c
iomfb_template.c
```

## RED and GREEN source gates

The retained evidence root is:

```text
/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn
```

The recipe identities are:

```text
827f23b12df8a4c97534e99d1a2127aa3d6ee58af6d04fccae3745b770620270  test_combined_candidate.py
2a30c015a9cf551d7f6b1b5753ae2983a4713804ce03b19c2779bf124e0433f1  test_build_contract.py
83c7bf35c9a2c6faa2df257f0089ba5c03d613b894f588dfe6dd736c5a33b3e4  build-appledrm.sh
7c36f8efc7f0937ba77fba60f9a0e6072db73538567ea6f9598303448dc4f83b  build-initramfs.py
```

The retained RED command is:

```bash
/usr/bin/python3 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test_combined_candidate.py \
  --source-root /home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux \
  --red-only
```

It exits 1 at the intended boundary:

```text
RED: AFK-only timeout crash store remains
```

The GREEN command omits `--red-only`. It verifies the exact source revision
and clean affected files. It applies both patches to a temporary copy. It
checks the exact changed-file set, 50 ms wait, timeout warning and return,
RTKit crash writer, atomic guard, and absence of new code comments. Five
negative mutations remove or alter one required boundary at a time. Each
mutation fails. The existing AFK lifecycle suite also runs unchanged.

The final output is:

```text
PASS: AFK opted-in quiescent service-slot reuse lifecycle
PASS: all RED controls failed; exact quiescent-retirement code passed
PASS: exact AFK lifecycle and PR582 timeout contracts passed
```

## Module build and comparison

The build used a new 582-entry tool manifest with SHA-256
`f50525a0b637d843bea4757bbb7ce402928d78517b3a7505f7823d66a69da1be`.
The sandbox runs as UID and GID 1001. It has no network, `/proc`, `/sys`,
`/boot`, `/home`, or `/run`. Inputs are read-only. The build uses the pinned
`7.1.6-1-1-ARCH` headers, `Module.symvers`, `vmlinux`, `pahole` 1.31, and
stock AppleDRM module.

The fresh control command was:

```bash
/usr/bin/python3 /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/sandbox.py \
  --manifest /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/toolchain-v7-afk-pr582-20260904.json \
  --input headers=/home/david/o/.dev147-stage/work/private-header-root/usr/lib/modules/7.1.6-1-1-ARCH/build \
  --input pahole=/home/david/o/.dev147-stage/usbdiag-d1c-20260828.cA1NXBKb1C/sandbox-tools/run-ck85xyae/work/pahole \
  --input afkpatch=/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/dev/apple-dp-altmode/afk-service-reuse/afk-service-reuse.patch \
  --input timeoutpatch=/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/dev/apple-dp-altmode/afk-service-reuse-pr582/pr582-timeout.patch \
  --input recipe=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/recipe \
  --input runtime=/home/david/o/.dev147-stage/usbdiag-d1c-20260828.cA1NXBKb1C/runtime-input \
  --input stockdir=/home/david/o/.dev147-stage/tipddiag-a2-20260829.5ShNpUnxf5/sandbox-tools/run-mvqmtbw_/work/t1-lookup-root/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/gpu/drm/apple \
  --input source=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/control-source \
  --input source-manifest=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/control-source.sha256 \
  -- /inputs/recipe/build-appledrm.sh control
```

The fresh combined command was:

```bash
/usr/bin/python3 /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/sandbox.py \
  --manifest /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/toolchain-v7-afk-pr582-20260904.json \
  --input headers=/home/david/o/.dev147-stage/work/private-header-root/usr/lib/modules/7.1.6-1-1-ARCH/build \
  --input pahole=/home/david/o/.dev147-stage/usbdiag-d1c-20260828.cA1NXBKb1C/sandbox-tools/run-ck85xyae/work/pahole \
  --input afkpatch=/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/dev/apple-dp-altmode/afk-service-reuse/afk-service-reuse.patch \
  --input timeoutpatch=/home/david/o/.dev147-stage/tipd-image-code-20260829.TPjkwkTaMa/worktree/dev/apple-dp-altmode/afk-service-reuse-pr582/pr582-timeout.patch \
  --input recipe=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/recipe \
  --input runtime=/home/david/o/.dev147-stage/usbdiag-d1c-20260828.cA1NXBKb1C/runtime-input \
  --input stockdir=/home/david/o/.dev147-stage/tipddiag-a2-20260829.5ShNpUnxf5/sandbox-tools/run-mvqmtbw_/work/t1-lookup-root/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/gpu/drm/apple \
  --input source=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/combined-source \
  --input source-manifest=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/combined-source.sha256 \
  -- /inputs/recipe/build-appledrm.sh combined
```

The fresh build runs are:

```text
control   /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/run-g70vss1j
combined  /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/run-3f1qx46e
```

Both exit 0 with unchanged inputs, no timeout, and empty build stderr. The
fresh control is byte-identical to the earlier independent control.

| Module | Bytes | SHA-256 | Build ID |
|---|---:|---|---|
| Fresh control | 8,744,352 | `c8fffa9a663760cb3c2f66f8d9123c76f01a6a5dfc51744ece1d36af1e54f7c3` | `8bc7a79d757fc70fbfae14ee050fc7c2353387ad` |
| Accepted AFK-only | 8,766,280 | `d6332afdf58f4af403201b7a6a469e1202f4370972f85a00054ecd563717d649` | `1ca52ad1cea00559d5fdfd32177e4d1e694994e1` |
| Combined | 8,766,768 | `602765912203e0c8860534c52f6447f8f393ba9b4cb2679af6246b82187c52d8` | `4d6d479dd0ffa6c8c418e410208e73ea2ec9abcf` |

The module name, vermagic, dependencies, aliases, and empty export set are
equal. The accepted AFK-only and combined import sets are identical. Compared
with control, they add only `_raw_spin_lock` and `_raw_spin_unlock`. The
decoded `apple_dcp` layout is readable in each module through both DWARF and
BTF. The corresponding decoded layout is equal across the control, accepted
AFK-only, and combined modules for each format. This check does not compare
the complete DWARF or BTF sections.

The control-to-AFK object delta is:

```text
afk.o appledrm.o audio.o av.o dcp.o dcp_backlight.o dptxep.o ibootep.o
iomfb.o iomfb_v12_3.o iomfb_v13_3.o parser.o systemep.o trace.o
```

The accepted-AFK-to-combined delta is only:

```text
appledrm.o iomfb_v12_3.o iomfb_v13_3.o
```

`iomfb_template.c` compiles into the two firmware-specific objects. The final
linked object also changes. No other AFK object changes between the accepted
AFK-only and combined builds. The focused comparison reports:

```text
PASS: module identities, metadata, ABI, layouts, and object deltas match the contract
```

## Non-default image

The image builder uses the accepted AFK-only image as its base:

```text
21,598,988 bytes
ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd
```

It replaces exactly this archive member:

```text
usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/gpu/drm/apple/appledrm.ko
```

The other 1,161 main archive records and the complete early archive remain
byte-identical. A negative run supplies the accepted AFK-only module to the
combined recipe. It exits 1 before it creates an image.

The successful image command was:

```bash
/usr/bin/python3 /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/sandbox.py \
  --manifest /home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/toolchain-v7-afk-pr582-20260904.json \
  --input base=/home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/run-935pw0qu/work/initramfs-linux-asahi-m2-displayport-afk-reuse.img \
  --input helper=/home/david/o/.dev147-stage/afk-reuse-build-20260902.vk13ijm06e/image-helper \
  --input moduledir=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/combined-build/apple \
  --input recipe=/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/image-recipe \
  -- /usr/bin/python3.14 -I -S -B /inputs/recipe/build-initramfs.py
```

The successful isolated run is
`/home/david/o/.dev147-stage/tipd-stage-a3-20260830.8r1yGjG8q9/sandbox-tools/run-ok0libbz`.
Its result is:

```text
PASS: AppleDRM-only AFK plus PR582 image built offline; nothing staged or loaded
```

The separate non-default artifact is:

```text
/home/david/o/.dev147-stage/afk-pr582-combined-offline-20260904.hdfiJZaOUn/image-build/initramfs-linux-asahi-m2-displayport-afk-pr582.img
21,599,177 bytes
3207dd0ff346765f4514b34a137c1c7456c459082463355e51047216dedc2867
```

It is mode 0600 and owned by UID and GID 1001. It is not in `/boot`.

This retained image is a mutable user-owned artifact. A privileged command
must not stage it directly by pathname. Before any sudo, staging, or reboot,
prepare and independently QA and review a new authenticated root publisher.
That publisher must pin the exact image hash and size, copy the image into a
fresh root-owned protected transaction, and verify the protected copy before
publication. The old AFK-only publisher is bound to different image bytes and
cannot be reused.

## Independent validation

Independent QA accepted the retained RED/GREEN source contracts, AFK lifecycle
coverage, module and image evidence, syntax, links, attributes, and whitespace.
Final review accepted the timeout semantics, artifact claims, attribution and
provenance, and the explicit mutable-artifact trust boundary. No blocker remains
in the offline candidate.

## Self-correction and limitations

Two preparation failures occurred before a successful compile. The old tool
manifest referred to a removed `libexpat` version. A first refreshed-manifest
run then rejected a malformed 63-character `libdw` hash. Both failures were
fail-closed. Neither started compilation. The new manifest and corrected hash
then passed both builds.

This evidence proves offline composition, control flow, build compatibility,
object scope, and one-member image transformation. It does not prove that the
50 ms timeout wrote the live crash flag. It does not prove physical display
reliability. Independent QA and final review accepted the offline candidate.
This result does not authorize privileged staging. A new authenticated root
publisher must pass independent QA and review before any sudo or staging. A
fresh attended boot must then restart display acceptance at generation 1.

No command in this slice used sudo, wrote `/boot`, staged an image, loaded a
module, changed the running kernel, rebooted, suspended, or requested a cable
or monitor action.
