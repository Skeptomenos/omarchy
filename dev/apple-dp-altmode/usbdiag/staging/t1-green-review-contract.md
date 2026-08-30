# A3 T1 staging helper — GREEN candidate review

Status: authored on 2026-08-30 after accepted semantic RED `run-qlfjssz8`; the GREEN candidate has not run. Root reports exactly three intended RED assertions, zero errors/skips, four successful fixture-only Bash children, outer exit 1, no timeout, unchanged inputs, 589 read-only mounts and seven smoke checks. The [frozen RED contract](t1-test-contracts.md), its exact inputs and the old C3 helpers/tests remain unchanged. Independent review and a fresh exact-input probe must precede the full GREEN run.

## Frozen candidate inputs

| Binding | SHA-256 |
|---|---|
| `/inputs/test`: [GREEN companion](test_stage_tipddiag_green.py) | `a5ba70013c382fd3d4ca700525c146f50cf9b70bf692498b72cb8d8d1c75b908` |
| `/inputs/helper`: [T1 public helper](../../stage-tipddiag-initramfs.sh) | `821d158a495b91462d7da5e338b9d2fb7f26d23ac66762a58d22a28948616e53` |
| `/inputs/baseline`: unchanged C3 public helper | `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| `/inputs/proof-spec`: unchanged independent eleven-proof specification | `189cde8a58dba21374cb7231342136ab25b97fb03ee1e755cdbb2d66a9119269` |

The four individual files are frozen privately in A3 `green-v1`. The GREEN test changes only the leading docstring and one `HELPER_SHA256` literal from [RED](test_stage_tipddiag_red.py). All 52 method sources and fixed expectations remain identical, including all 38 historical real-file methods. Neither test binds a real image, operational helper, complete source tree, boot tree or hardware tree.

## Minimal implementation delta

The new standalone helper preserves C3's `D2ST_`/`d2stage_` interfaces and file-transaction algorithms. It binds the accepted T1 image: 19,209,545 bytes, SHA `c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe`, with distinct destination `/boot/initramfs-linux-asahi-dpalt-tipddiag1.img`, temporary basename and staging-directory label. Completion text names a T1 TIPD diagnostic, says it is untested at startup, preserves normal boot and grants no reboot permission.

All 33 C3 protected records stay unchanged. One staged-E row is added. The eleven literal proof records bind the accepted source/module/build proof, three accepted E proof JSON files from `run-988kuwr1`, and five assembly result/command/input/security/outer-result records from `run-mvqmtbw_`. The exact 34 + 11 producer contract has 45 unique paths. No future package seal or inferred proof is accepted.

The new power validator requires exactly two arguments and both must be literal `1`. Preflight reads the two fixed retained paths, `/sys/class/power_supply/macsmc-ac/online` and `/sys/class/power_supply/tps6598x-source-psy-0-003a/online`, after the unchanged battery-above-50 check and before `/boot` checks. No reader has run. The synthetic validator rejects multiline strings, but command substitution strips trailing newlines; this is not raw-file trailing-newline validation. Software online values are not physical MagSafe, active-charging or isolated-charging proof.

Copy, single-link identity continuity during copy, no-replace publication, sync, incomplete markers, exit trap, environment rejection, kernel/package/root guards and reserve checks retain their reviewed C3 algorithms. No argument, environment, path, retry or cleanup override is added. As before, later preflight hash checks do not prove inode continuity across the whole staging invocation or defeat an adversarial source race. Final-file or provisional-result presence alone is not completion.

## Private-copy gate

The private operational helper SHA is `f1b308389e14fd9b341f2a3f8bd0a526501e1a86cfcdc2acdbd3992919a6bcce`. Its only changes from the public candidate are the exact SOURCE, PROOFS and ROOT_UUID assignments. SOURCE/PROOFS point directly to the retained A2 tree and sole accepted assembly. The UUID comes from the unchanged private C3 helper, not a live read, and stays private. An exact byte comparison confirmed only those three assignment changes; independent comparison remains required. Any edit invalidates the comparison. No operational helper or preflight was executed.

The A4 seal will bind the finished package externally. The helper does not consume a seal containing itself. Private output permissions, exact source/proof paths and every artifact pin must be checked in the later private-copy review. No public placeholder may be filled by an argument or environment variable.

## Proposed full GREEN command

After independent review and a fresh successful exact-four-input probe, the root task may approve this syntax-gated workload in the unchanged v5 fixture runtime:

```text
/usr/bin/bash -c '/usr/bin/bash -n /inputs/helper && exec /usr/bin/python3.14 -I -S -B /inputs/test'
```

Expected: all 52 methods pass, zero failures/errors/skips, successful setup and post-input authentication, no timeout, unchanged outer inputs, exact retained fixture child triplets and no remaining workload. The four task bindings give 589 read-only mounts. The existing 280-second launcher deadline and 285-second outer cap remain. No command in this contract has run as part of GREEN authoring.

Full private-file tests cover the actual start/hash/copy/recheck/publish/recheck/finish sequence; protected sentinel bytes and metadata; exit 7 after copy and after publication; closed stdout after the completion-marker transition; and temporary/result/final-marker collisions. Expected failures must retain outputs and `INCOMPLETE`; they do not permit retry or repair. Real-file tests do not prove root preflight, storage power-loss safety, physical power state, kernel behavior or boot safety.

All production preflight, staging, sudo, reboot, cable, device, recovery-rehearsal and live-action holds remain active. A staging-helper PASS will be a partial A3 checkpoint only. The fixed-profile bounded capture/binding implementation still needs its separate software-only RED/GREEN and review before a complete manual test package can be ready. The unsafe aggregate-test hold and historical failures remain visible.
