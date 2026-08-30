# DEV-147 private T1 image assembly — 2026-08-30

Scope: the one authorized, contained, unprivileged offline T1 assembly.
Result: private assembly PASS and independent read-only result QA PASS.
This is not staging, startup, hardware or reliability evidence.

## Authorization and retained sequence

The root task ran the entry once after independent pre-execution review PASS
and a fresh exact-input v5 probe. The earlier [source/fixture checkpoint](dev-147-t1-assembly-preexecution-2026-08-30.md)
remains historical. Its RED `run-od4kokms`, GREEN `run-_6v39awz`, and later
independent QA `run-zbpyg548` were zero-child tests, not image assembly.
Independent QA passed all three methods before this production entry ran.

| Run | Observed result |
|---|---|
| `run-vpqm7rk3` | Fresh exact-nine-input isolation probe PASS; outer exit 0, no timeout, unchanged inputs, 594 read-only mounts. |
| `run-mvqmtbw_` | Sole actual T1 assembly; outer exit 0, no timeout, unchanged inputs, the same 594 read-only mounts. All six planned children completed with exit 0 and empty stderr. |

The probe and assembly have byte-identical input and security records. No
assembly retry occurred. No relevant process remained after the run. The
exact host commands, input paths, raw logs and outputs stay private.

## Fixed source and input identities

| Input | SHA-256 |
|---|---|
| Dedicated `assemble_t1.py` | `0facf27332e698bb24826a63b617e899d18bd591f399d869c5c91f12bb2f5552` |
| Frozen `test_assemble_t1.py` | `03c5a8c0d1526d27c6cb78dfd739e878104850f25d33d6078d7723feb0877fc6` |
| Pure `image_contract.py` | `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf` |
| `prepare_image.py` | `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60` |
| `verify_control.py` | `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8` |
| `cpio_image.py` | `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58` |
| Accepted T1 `core.c` | `215051ed006431c73f2e402e5a1d503daaa41dc9d4b9e2bb66a82ac868892a92` |
| Accepted T1 module, 1,327,920 bytes | `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f` |
| Accepted T1 build evidence | `95abe335e44a5f30781a1e80f3e26efc314746b5d6baf11bae658f4484d9ada3` |
| Retained E base, 19,191,513 bytes | `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae` |
| Accepted E header | `1665fe5a0d5d58eb3fa029faaea066da5c4b026415d19c33d644c5ec0b44f96a` |
| Accepted E evidence | `6bbbb024d616bfa767dfe71b4a6121a1e75233bb1a1c8bc47b81b93f28628709` |
| Accepted E result | `5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2` |
| Accepted E recipe | `1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77` |
| Private launcher | `62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827` |
| Toolchain-v5, 582 runtime entries | `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0` |

The [fixed assembly contract](../../dev/apple-dp-altmode/usbdiag/tipd-image/t1-assembly-contract.md)
owns the nine binding names, six exact commands, validation and failure rules.
The E proof binding is the accepted `run-988kuwr1` work directory. The entry
reads only its three pinned JSON proofs. It reuses their authenticated 424
recorded reports and descriptors. It does not reread all 1,272 prior raw child
files or rerun E. The T1 candidate was never bound into an E control. The two
failed E attempts remain preserved by the [accepted third-attempt record](dev-147-e-operational-third-attempt-pass-2026-08-30.md).

## Actual output and readback

| Private output | Size | SHA-256 |
|---|---:|---|
| `initramfs-linux-asahi-dpalt-tipddiag1.img` | 19,209,545 bytes | `c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe` |
| `t1-assembly-result.json` | 7,442 bytes | `10e0ad4b37efab56d04d910f959a6acb5ac53db6f8b1e04efdab91943f1d26c5` |

Both outputs are mode `0600`, owner/group `1001:1001`, and single-link. The
complete result reports `PASS`, `offline: true`, and `image_created: true`.
It reports `staged`, `module_loaded`, `rebooted`, and `boot_tested` as `false`.

The parsed image has seven early records and 1,163 main records. Exactly one
payload changed: `usr/lib/modules/7.1.6-1-1-ARCH/kernel/drivers/usb/typec/tipd/tps6598x-core.ko`,
from SHA `bc02723db427639c6586d29eea7918e084874c741b60bf145585c6349fd07d70`
to the accepted T1 module SHA above. The other 1,162 main raw records, archive
order/trailer and 244-byte tail, 10,240-byte early archive, and all seven index
payloads stayed byte-identical.

The gzip child used exact `-n`. Its 61,400,828-byte input equals the saved
decompressed main archive. That archive SHA is
`2be5aaa3fcd979aa8204e2c00e3e839f7da3e8ba54b1aac86c940e33a6b94a4f`.
The root task's additional read-only gzip integrity check passed. The
compressed main header is `1f8b0800000000000003`, with zero MTIME.

Direct `readelf -n` output showed build ID
`40aa54382047ba36b02c9ac0da65a213862a77ad`. The private lookup tree held
207 files and 48 directories: 200 module payloads and seven retained indexes.
Independent QA matched their bytes and metadata to the final image. Exact `modinfo`
filename/name/depends checks passed. The dry-run dependency output described
`typec.ko` then the T1 `tps6598x-core.ko`, with one trailing ASCII space per
`insmod` line. No module was loaded. No `depmod` or index generation ran.

## Run-record identities

| Record | SHA-256 |
|---|---|
| Probe command | `1dfa8d2f2473a8dd04faf5769f89a4b6d81a41bd0a45a09bd1d9dc70ca4d4551` |
| Assembly command | `c11ec0dc7d39dad155a75fe32c72edad6620506fa3f842f76549322a5360a4d4` |
| Both input records | `c41b8de09b6bf2c08877af36fd48604309d8d1bfec2204a93d4cf0f51836fd59` |
| Both security records | `eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2` |
| Both outer results | `995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f` |

## Acceptance and holds

Independent read-only result QA reported zero failures and final PASS. It
checked all 594 current input fingerprints, exact probe/assembly input,
security and command models, gzip CRC/size/single-stream integrity, actual ELF
build ID, the single-payload delta, all six child triplets and exact outputs,
the lookup tree, result descriptors and flags, and the exact 26-member output
set. No relevant process remained. QA did not rerun assembly or alter files.
This was a focused result audit, not a full repository-suite run. The unsafe
real-home aggregate-test hold and its five historical failures remain.

Final-file presence is not acceptance. This private gate requires complete
validated JSON, outer exit 0, no timeout, unchanged inputs, and independent
candidate/readback audit.
The exclusive final-result write is not atomic publication; a failed write or
fsync can retain a partial or complete final-path file. No failure cleanup or
retry is authorized.

The next work is the separately reviewed offline A3/A4 manual-boundary
package, not use of this image. Every sudo, installed-module,
`/boot`, `/etc`, staging, live-module, reboot, cable, device, recovery-rehearsal
and hardware action remains HOLD. All historical images, modules, proofs and
seals remain retained. No live state changed, so no live rollback was needed.
