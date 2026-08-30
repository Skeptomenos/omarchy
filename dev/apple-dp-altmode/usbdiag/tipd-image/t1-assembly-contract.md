# Fixed T1 assembly boundary

Reconciled: 2026-08-30. The [sole private assembly](../../../../docs/evidence/dev-147-t1-private-image-2026-08-30.md)
and independent read-only result QA passed. Fresh probe `run-vpqm7rk3` preceded
assembly `run-mvqmtbw_`; both exited 0 without timeout or input change. The
private T1 image exists. It is not staged, loaded, booted or hardware-tested.
Next: offline A3 handoff-package preparation and review. All live/manual holds
remain active.

The historical [pre-execution checkpoint](../../../../docs/evidence/dev-147-t1-assembly-preexecution-2026-08-30.md)
owns the RED/GREEN test hashes and runs. Independent QA `run-zbpyg548` passed
3/3 with outer exit 0, no timeout, all 595 input fingerprints unchanged, and
zero children, image or assembly result. Safe baseline checks passed 453 Bash
and 5 Python syntax checks plus 455 command-metadata entries. The aggregate
suite remains unrun under the unsafe real-home test hold; its five historical
failures are not erased. Independent pre-execution review and the fresh
exact-input v5 probe passed before the sole private entry ran. No retry follows.

## Fixed inputs

The dedicated [assembler](assemble_t1.py) accepts no arguments or environment
overrides. It uses these nine read-only bindings. The launcher adds its fixed
proof binding and runtime, giving 594 read-only mounts. The test adds one
runner binding, giving 595 mounts. A test binding cannot enter production.

| Binding | Fixed content |
|---|---|
| `/inputs/recipe` | `assemble_t1.py`, SHA `0facf27332e698bb24826a63b617e899d18bd591f399d869c5c91f12bb2f5552` |
| `/inputs/contract/image_contract.py` | Pure contract, SHA `a1eda280aa56967aa06b01a2cca0dfc70c3da6df25066f8a1e815beec719f1bf` |
| `/inputs/assembly/prepare_image.py` | Existing pure gzip function/import chain, SHA `00caceb3b7fa236dcc030fb4007d0baa75bfa08fcd1590626f85fcc8c22d5f60` |
| `/inputs/control/verify_control.py` | Existing reviewed child runner and index selector, SHA `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8` |
| `/inputs/helper/cpio_image.py` | Existing parser/replacer and file guards, SHA `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58` |
| `/inputs/base` | Retained E: 19,191,513 bytes, SHA `4d4f0557af57eebcc33322f004bcc7968254e644b069a11102375df0b31a52ae` |
| `/inputs/module` | Accepted private T1: 1,327,920 bytes, SHA `a0fdadc351261643545e5afd8561923be99431661c447084336c9318f5b0c02f` |
| `/inputs/build-proof` | Build evidence SHA `95abe335e44a5f30781a1e80f3e26efc314746b5d6baf11bae658f4484d9ada3` |
| `/inputs/e-proof` | Accepted E work directory from `run-988kuwr1`; the entry reads only its three pinned published JSON proofs |

The four source directories contain exactly their one named file. Reads are
bounded, no-follow, regular and single-link. They check file and parent
identities. All four source bytes authenticate before any dependency executes.
The unchanged pure contract remains historically unbound; the new dedicated
entry supplies the fixed operational identities. It never calls an old main.

The three E proof hashes are header
`1665fe5a0d5d58eb3fa029faaea066da5c4b026415d19c33d644c5ec0b44f96a`, evidence
`6bbbb024d616bfa767dfe71b4a6121a1e75233bb1a1c8bc47b81b93f28628709`, and result
`5e08a383469bd65d402939d0b7ca9cef9c2febb77ca12de1d577454b0d2de8f2`.
The code validates the exact accepted proof chain and its recorded 424 reports
and descriptors. It reuses authenticated accepted evidence; it does not reread
the 1,272 raw prior child files or rerun E. The accepted E recipe SHA is
`1be81904b29c69cb24fae86208c62fb30e830eca46250978a65d8ed19db8de77`.

## Exact offline child plan

The six fixed commands are:

```text
/usr/bin/gzip -n
/usr/bin/readelf -n /inputs/module
/usr/bin/modinfo -b /work/t1-lookup-root -k 7.1.6-1-1-ARCH -F filename tps6598x_core
/usr/bin/modinfo -b /work/t1-lookup-root -k 7.1.6-1-1-ARCH -F name tps6598x_core
/usr/bin/modinfo -b /work/t1-lookup-root -k 7.1.6-1-1-ARCH -F depends tps6598x_core
/usr/bin/modprobe --dry-run --show-depends -d /work/t1-lookup-root -S 7.1.6-1-1-ARCH -C /work/t1-empty-modprobe.conf tps6598x_core
```

Gzip receives only the transformed main archive on stdin. Bare gzip is not in
the plan. The reviewed child runner retains stdout, stderr and result files,
uses a 90-second child timeout, and rejects failure or nonempty stderr. The
32 MiB gzip and 64 KiB descriptor-output limits are post-exit acceptance
checks, not live streaming byte caps. The runtime caps are the child timeout
and the launcher's unchanged 280-second deadline with a 285-second outer cap.

The build-ID parser requires one exact
`40aa54382047ba36b02c9ac0da65a213862a77ad` line. The private lookup root contains
200 module payloads from the final parsed archive and the seven retained
indexes. No `depmod` or index generation runs. Exact lookup output must name
the T1 path, module `tps6598x_core`, dependency `typec`, and two ordered dry-run
`insmod` lines: `typec.ko`, then `tps6598x-core.ko`. Each `insmod` line has one
trailing ASCII space. Missing/doubled spaces, reordered paths or extras fail.
The checks preserve file identities and bytes, including the empty
configuration. They check directory membership, mode and owner, but do not
prove directory-inode persistence across calls.

## Output and failure boundary

Only the TIPD core payload may change. The pure `archive_delta` check must
preserve every other raw record, order, trailer/tail, early archive and all
seven index payloads. Fresh readback independently reparses the saved image
and repeats the delta and lookup-root checks. All immutable input bytes and
identities are rechecked after image readback.

The exclusive output is `/work/initramfs-linux-asahi-dpalt-tipddiag1.img`.
The exclusive `/work/t1-assembly-result.json` is published last. It must state
`staged`, `module_loaded`, `rebooted` and `boot_tested` as `false`. A failure
retains partial files. A publication or fsync failure can leave a partial or
complete file at the final result path. File presence alone is never PASS.
This is exclusive creation, not atomic publication. Acceptance requires
complete validated result JSON, outer exit 0, no timeout, the launcher's
unchanged-input result, and an independent audit of the candidate/readback.
The final pathname alone never authorizes use. No cleanup or retry exists.
There is no staging path, live module action, device access or boot step. A
successful private assembly is not hardware evidence.

The [three-method test](test_assemble_t1.py) authenticates real fixed inputs,
tests validators and exact policy/refusal cases, and inspects the publication
shape. It never calls the production entry, runs a child, replaces a payload
or creates an image. It supplements the unchanged 15-method archive suite;
it is not end-to-end assembler execution coverage. The existing typed
stdlib/dataclass/unittest no-install exception applies. No new dependency or
full repository suite result is claimed.
