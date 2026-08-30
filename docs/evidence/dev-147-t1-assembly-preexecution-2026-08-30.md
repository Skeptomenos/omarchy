# DEV-147 T1 assembly pre-execution checkpoint — 2026-08-30

Scope: contained, unprivileged offline source and fixture work only.
Result: one genuine semantic RED and one fresh zero-child GREEN. No T1 image,
production assembler child, staging, load, boot or hardware result exists.
Branch: `codex/dev-147-t1-image-offline`, starting at `75f541ff283be8242cc494f9da28fc88d87210c1`.

## Retained sequence

| Run | Exact sources and result |
|---|---|
| `run-od4kokms` | Incomplete assembler SHA `06177853426abad2d829141f2814d98e838e22d88764560c86305e6de6ead5a3`; test SHA `852a03b13cd683f120b921d0423345cad60db639f9060bf5d9c0d63646ffd436`. Setup/authentication passed. Three tests produced exactly three intended assertions: missing policy, missing validated inputs, and missing fixed main entry. Exit 1; zero errors/skips. |
| `run-_6v39awz` | Assembler SHA `0facf27332e698bb24826a63b617e899d18bd591f399d869c5c91f12bb2f5552`; test SHA `03c5a8c0d1526d27c6cb78dfd739e878104850f25d33d6078d7723feb0877fc6`. Setup passed. Three tests passed in 0.304 seconds. Exit 0; zero failures/errors/skips. |

Each run used the exact toolchain-v5 manifest and 595 read-only mounts. Each
reported unchanged inputs and no timeout. Each executed zero assembler or
production children. Each retained only probe/sentinel/log files and a
distinct `/work/t1-assembly-fixtures/test-result.json`. Neither created a
lookup root/configuration, child record, `.img`, or T1 assembly result.

The RED source snapshot is retained privately as `t1-assembly-red-v1` in the
private code-stage directory. It preserves the exact 71-line incomplete
subject and 215-line test. The RED completed at approximately 02:49
Europe/Berlin. At approximately 02:52, the living test changed the four
dependency bindings from direct files to one-file directories and added nine
build-ID parser assertion lines. That intermediate test SHA was
`0c5fb4511749887c98dddaba36b79efbac4e2382ea3ce18f38d4bf1b42cda9b8`.
The exact earlier snapshot was reconstructed and hash-verified before the
GREEN subject changed. No RED rerun occurred. The private snapshot note SHA is
`edfe136c2774d93133fcbc3aa9f6dfac08ca902e993e52f40fc005c5eef02270`.
Independent QA accepted the frozen RED and disclosed the post-run test drift.

## Tested boundary

The [fixed assembly contract](../../dev/apple-dp-altmode/usbdiag/tipd-image/t1-assembly-contract.md)
owns the nine bindings, exact pins, six-command plan and publication order.
The existing pure archive contract and its three source dependencies were not
changed. The new dedicated assembler supplies the fixed operational pins.

The zero-child GREEN authenticates real E, T1 module and build evidence, and
the three exact published E proof JSON files. It validates the recorded 424
E reports/descriptors and accepted proof flags. This is reuse of authenticated
accepted E evidence, not a new audit of all raw prior child files and not a
rerun of E. The read-only `/inputs/e-proof` binding is the accepted E work
directory; the entry reads only the three pinned JSON proof files from it.
The T1 candidate was never an input to an E control.

The tests cover exact fixed bindings/commands/output names; build-ID line
refusal; exact filename/name/depends and dry-run grammar; changed build proof
and E proof bytes; descriptor path/hash/mode/owner/link/count refusal; and the
fixed final-publication AST shape. No test calls the production entry or
assembles an in-memory or on-disk T1 image. The unchanged 15-method pure
archive suite owns the structural replacement and file-primitive coverage.

AST parsing and `py_compile` passed for both new Python files. Compilation
outputs are retained in a separate private static-check directory. No module
was imported by the host compile check. The standard-library/dataclass/unittest
exception remains explicit. No package, launcher or toolchain changed.

## Retained identities

| Record | SHA-256 |
|---|---|
| Private launcher | `62d3c8224cdf2add93a96195f2d35da232086b7074911c92346cd3200beee827` |
| Toolchain-v5, 582 runtime entries | `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0` |
| GREEN command record | `ca39373d36cc29710c6409fdf6d304040a4e89d9917fb16056f180f2ede42e4d` |
| GREEN input record | `9efe5a9fa6e3bf47b07ebd626540b50278893e4b22c776fb281028497545544f` |
| GREEN outer result | `995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f` |
| GREEN security record | `eb52e8d04db7a847c19dc68e57f5b1b1331c46c45852100dc3ae19d7e9da96f2` |
| GREEN test result | `9a404d91d3bffa45daad87b03a0dcb30c9e8d597f73658516a9fc19fcc035282` |

Full host-path commands, bindings, raw logs, snapshots and run directories stay
private. The proposed nine-binding command is a review artifact, not evidence
of execution. It would have 594 read-only mounts and six bounded offline
children. It is not the historical 424-child E command.

## Holds and next gate

Independent GREEN QA and pre-execution review were pending when this immutable
checkpoint was written. The living plans own later verdicts. Before any real
assembly, the root task must review the frozen source/test, exact nine inputs,
source/proof/module pins, private output and failure retention, then require
a fresh exact-input v5 probe. A failure stops the gate; it does not permit a
retry or broader action.

Every sudo, installed-module, `/boot`, `/etc`, staging, live-module, reboot,
cable, device, recovery-rehearsal and hardware action remains HOLD. The source
implements a private assembly boundary only. No recovery or rollback is needed
for this source/fixture work, which changed no live system state.
