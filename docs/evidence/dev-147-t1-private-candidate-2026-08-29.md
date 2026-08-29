# DEV-147 T1 private candidate evidence — 2026-08-29

Status: immutable dated evidence. This note records the accepted private T1
module candidate. It does not record an image or hardware result.

The canonical private record is `a2-candidate-build-evidence.json`, SHA-256
`95abe335e44a5f30781a1e80f3e26efc314746b5d6baf11bae658f4484d9ada3`.
Its filesystem path remains private.

## Source identity

The retained private source directory is `candidate-source-v1`. It remains in
the private evidence area. Its `core.c` SHA-256 is
`215051ed006431c73f2e402e5a1d503daaa41dc9d4b9e2bb66a82ac868892a92`.
Do not publish or infer its private path from this note.

## Contained build evidence

Two contained builds produced byte-identical `tps6598x-core.ko` files:

| Run ID | Exit | Result |
|---|---:|---|
| `run-hijfq2nz` | 1 | The module built successfully. The run then stopped because its stale expected-import list differed from the observed list. |
| `run-zgkw4hqf` | 0 | The corrected independent inspection passed with 592 read-only bindings. It reported 99 strong imports, 9 exports, and unchanged `cd321x`, `tipd_data`, and `tps6598x` DWARF and BTF layouts. |

Both module outputs have these exact identities:

| Property | Value |
|---|---|
| SHA-256 | `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f` |
| Size | 1,327,920 bytes |
| Build ID | `40aa54382047ba36b02c9ac0da65a213862a77ad` |

The accepted run confirmed common DWARF and BTF sizes of 680 bytes for
`cd321x`, 120 bytes for `tipd_data`, and 384 bytes for `tps6598x`. Its exact
table review covered all four retained TIPD tables, 27 export-relocation rows,
and every stored binding, type, and addend. It also confirmed that the five
added strong imports came only from fixed `vmlinux` export rows and added no
module dependency.

Both runs kept their inputs unchanged. Neither run timed out. The accepted
record states that the second fresh `/work/candidate` build was byte-identical
to the first compiled build and that `cmp` exited 0. The first exit 1 is
retained setup/inspection history. It is not a failed compilation and is not
relabelled as GREEN.

## Boundary and holds

The module is an accepted private offline candidate. It was never bound into
production attempt `run-f2yoto48` or any other E-control run. No T1 image was
assembled. The module was not loaded, staged, or booted. It has no display,
USB, charging, suspend, startup, or other hardware result.

T1 image assembly remains on HOLD until a fresh E-control PASS. Independent
final review, a separate GO, and a fresh toolchain-v5 probe remain required
before any second E-control production attempt. All image-build, load, stage,
sudo, reboot, cable, device, recovery-rehearsal, sysfs, boot-file, and
live-system holds remain active.
