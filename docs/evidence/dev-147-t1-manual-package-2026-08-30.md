# DEV-147 T1 manual-boundary package — 2026-08-30

Status: the private package passed independent handoff, manifest, safety, and final checksum review and is integrity-sealed. It is ready only for David's first manual staging/review boundary. No command in the package is released by this record.

## Scope and result

David authorized completion of the held handoff and seal after accepting the lean remaining path. The package reuses the accepted T1 module and image, the 54-method staging-fixture result, and the 13-method fixed collector/binding result. No source, runtime, image, helper, test, or accepted artifact changed. No build, assembly, fixture suite, live collector, staging, boot, or recovery action occurred. The unrestricted `./test/all` remains UNRUN/HOLD.

The sealed inventory contains 86 retained references, 43 accepted pins, and 49,051,633 referenced bytes. The seal covers 89 members: the 86 references plus `HELD-HANDOFF.md`, `REFERENCES.json`, and `REVIEWS.md`. Independent handoff, reference-manifest, and safety review passed. Root and final independent checksum QA each ran `sha256sum --strict --check` against the private seal: exit 0, all 89 members OK. Independent QA confirmed exact membership, package-directory mode 0700, and four package files at mode 0600 with one link and the expected owner.

- Frozen handoff SHA-256: `1f700c2f623040b7dbc34c1c24679de49cbeb0294017698c61d64e5ddc624db3`.
- `SHA256SUMS` SHA-256: `72180f0c92182db2b94fe7851b3ad27ed0c417fdd9e438c38498ca0447fd1c45`.

This is a checksum snapshot of retained private inputs. It does not authenticate current `/boot`, EFI, tools, power state, cable state, or storage durability. It does not prove that T1 is staged, selected, booted, or captured. It is not a display, USB, charging, reliability, recovery-runtime, or overall monitor-fix result.

## Current boundary

STOP before staging. A staging-only release needs fresh confirmation that David is present, work is saved, Linux and the internal display are responsive, the lid is open, battery is above 50%, physical MagSafe is connected, and the cable/device state is recorded. The monitor need not be newly connected for staging. Fresh source/input authentication and drift stops still apply.

Any later attended T1 boot, fixed live capture, or conditional recovery needs a separate explicit release, the offline recovery guide, fresh readiness checks, and an authenticated caller. There is no automatic retry or test ladder. All sudo, staging, live journal/hardware/power/cable/device, reboot/suspend, recovery-rehearsal, runtime-expansion, and upstream-submission holds remain active.
