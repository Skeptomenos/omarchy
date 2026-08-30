# DEV-147 T1 staging preparation HOLD — 2026-08-30

Scope: unprivileged offline A3 preparation for the existing M2 diagnostic. David authorized offline preparation only. No production preflight, staging, sudo, reboot, cable/device action or recovery rehearsal was authorized. Source work used `codex/dev-147-t1-image-offline`, based on `81c187895f0ff710b72b74d1479b64545a8061bf`.

## What happened

| Retained checkpoint | Observed result |
|---|---|
| Initial fresh probe `run-jo8q59ie`, then staging RED `run-qlfjssz8` | Probe passed. Three selected tests reached exactly three intended assertion failures after successful authentication/setup; zero errors/skips. Four fixture Bash children exited 0 with empty stderr. RED outer exit 1, no timeout, unchanged inputs, 589 read-only mounts and seven smoke checks. Root and independent QA accepted the semantic RED; the private `a3-staging-red-independent-qa.json` retains that audit. |
| GREEN-v1 pre-execution review | No GREEN workload ran. Review found a literal private proof root in the public operational guard and no sync in the current runtime. Preserve this rejected, unexecuted version and its private operational copy. |
| Privacy probe `run-pd9_sz89`, then RED `run-l7r97oh1` | Two selected tests reached exactly two intended assertions: exposed root text and a deliberate no-op predicate accepting a nonexact string. Zero errors/skips; two fixture Bash children exited 0 with empty stdout/stderr. Setup/post-input checks passed; outer exit 1, no timeout, unchanged inputs and 589 mounts. Root and independent QA accepted the retained RED. |
| Corrected GREEN-v2 probe `run-n0c0ncqz` | Exit 0, seven smoke checks, empty stderr, unchanged inputs and 589 read-only mounts. |
| Sole syntax/seven-method subset `run-5ge704kx` | Syntax passed; seven tests passed in 0.182 seconds, with zero failures/errors/skips. Outer exit 0, no timeout, unchanged inputs and successful setup/post-input checks. Root audited all 37 child triplets. Independent read-only result QA passed without rerunning the subset. |

The first RED used an exact C3-derived incomplete subject with a no-op power interface. The privacy RED preserved all 52 prior test bodies and added two methods against a documented no-op root predicate. GREEN-v2 changes only that predicate and its operational guard wiring from rejected v1. Its companion changes only the docstring and helper pin from privacy RED; all 54 method bodies remain unchanged. The root predicate hashes the exact supplied string without reading or normalizing a filesystem path. Public SOURCE/PROOFS/ROOT_UUID assignments remain deliberately invalid. The separate private operational-v2 copy differs by exactly those three assignments and has not run.

## Focused result and fixed pins

The [reviewed subset contract](../../dev/apple-dp-altmode/usbdiag/staging/t1-privacy-green-review-contract.md) owns the exact syntax-gated seven-method command. It covers public privacy/static wiring, exact root-string validation, fixed T1 image names/identity, old 33 protected rows plus staged E, eleven A2 proofs and strict external-power values/static reader wiring. It does not run the file transaction or production readers.

The 37 fixture Bash children were seven exit-0 results and thirty expected exit-1 refusals. All stdout/stderr and saved child triplets matched the assertions; none timed out. Five successful producer outputs had five image-identity lines, 33 baseline rows, 34 protected rows twice and eleven proof rows. The two successful predicate calls had empty streams. The refusal calls emitted their fixed errors and no stdout. Independent read-only QA confirmed the exact command/stream records, 34 protected plus eleven proof paths with 45 unique combined paths, unchanged input fingerprints, no unexpected image/staging output and no surviving workload. It audited the retained run without a rerun. No real image, production preflight, staging output or new live observation was used.

| Source or record | SHA-256 |
|---|---|
| [Public/helper GREEN-v2](../../dev/apple-dp-altmode/stage-tipddiag-initramfs.sh) | `91553641af7e6676c8c032cb3432406fec3958959674ec5917a759726714c71e` |
| [Seven-method companion within the unchanged 54-method suite](../../dev/apple-dp-altmode/usbdiag/staging/test_stage_tipddiag_privacy_green.py) | `af28433894b92728a7a1892b543e10b59e2d0ff6c5e359a8ba390ec62f9563b0` |
| Frozen C3 baseline | `dbfbeac043d77ed1543274322f4f961a7622a2adbf49503bb2f54ee465d4d6fe` |
| Independent private proof specification | `189cde8a58dba21374cb7231342136ab25b97fb03ee1e755cdbb2d66a9119269` |
| Private operational-v2, not executed | `6b20d119791f4322e101a92b9e5b850ba3098d35dbf966f2d7918cb3918694f9` |
| Unchanged 582-entry v5 manifest | `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0` |
| Shared GREEN probe/subset `inputs.json` | `83e67add724522b647396c01ad0c16e8d6ad0e629902bda066a58d778138a231` |
| Successful outer `result.json` | `995626ca50174bc34f03fdf59825ddb8c485ffcb59d62d20116b394620ac3a1f` |
| Subset unittest stderr | `35f5fbc9f42cf6d58501f82738b9e7e1c005b21b26e101bc3954f47c361702fc` |

The two new private directories are 0700 and their six files are 0600, single-link and owned by UID/GID 1001. Public source files remain 0644. Earlier RED, rejected GREEN-v1, operational-v1 and privacy RED snapshots remain unchanged. Their authored-time contracts stay historical: [initial RED](../../dev/apple-dp-altmode/usbdiag/staging/t1-test-contracts.md), [v1 review](../../dev/apple-dp-altmode/usbdiag/staging/t1-green-review-contract.md) and [privacy RED](../../dev/apple-dp-altmode/usbdiag/staging/t1-privacy-red-contract.md).

## Runtime approval boundary

The private `a3-runtime-dependency-hold.json`, SHA `100c75fdf3639e22c5a58167f43113a841d5ccb0a0f5b4937d573b90a02f7d62`, records the independently checked prerequisite facts. V5 has 582 runtime entries and lacks `/usr/bin/sync`. Full 54-method GREEN is UNRUN/HOLD.

The unapproved minimal proposal preserves all 582 v5 rows exactly and adds only the historically pinned sync, SHA `bf77551deae42b2d0aa5eaede07a8f9c2954409fe38ea79af2b0a238880c899c`. That would give 583 runtime entries and 590 read-only mounts with four task inputs. Its loader and libc already match v5; no new library, directory, device or writable binding is proposed. The whole historical manifest must not be reused because its libgcrypt row differs from accepted v5.

Sync -f flushes the containing filesystem, not only the named synthetic file. Unchanged writable bindings do not imply fixture-only I/O effects. Separate user approval, exact manifest review and a fresh probe are required before this addition or the full suite. No expanded manifest was created. The copied v5 content stayed unchanged, and no sync ran in this A3 checkpoint. No fake sync, relaxed helper, host-tool fallback or broader mount is allowed.

## Open and retained state

The accepted [private T1 image](dev-147-t1-private-image-2026-08-30.md) remains unchanged and unstaged. The seven-method subset is not full staging GREEN, a full A3/A4 package, overall goal completion, boot safety or hardware acceptance. Its synthetic power validator/static wiring does not establish physical MagSafe, active charging, isolated charging or raw-file newline rejection.

The accepted capture package has 21 pure tests, not a working collector. Its operational collection/binding entry remains closed. A new fixed-profile bounded collector and exact T1 artifact binding still need implementation, genuine RED/GREEN and independent review. Reviewed private capture, one-case and recovery drafts are not release instructions. A structurally complete trace prefix cannot rule out a wholly absent closed suffix or prove receiver delivery.

No machine rollback was performed or needed for this private-source/documentation checkpoint. Preserve all prior images, helpers, snapshots, seals and backups; do not clean up or replay old commands. The unsafe aggregate-test hold remains. All production preflight, staging, sudo, reboot, cable/device, live-action and recovery-rehearsal holds remain active. The [main plan](../plans/dev-147-m2-displayport.md#current-state--display-recovery-observed-living) separately owns David's later overnight battery-depletion report and its unproved timing/cause.
