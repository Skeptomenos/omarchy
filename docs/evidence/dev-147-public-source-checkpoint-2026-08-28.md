# DEV-147 public-source checkpoint — 2026-08-28

Status: pre-publication source checkpoint and initial isolated RED results. No commit or push result is claimed in this record. The [main plan](../plans/dev-147-m2-displayport.md) owns current status; the [diagnostic plan](../plans/dev-147-usb-startup-diagnostic.md) owns remaining offline D1 work.

Approval: David asked to commit and push all task work, then proceed. Offline implementation, focused QA, and private module/image preparation were already approved. Staging, live driver operations, package installation, and reboot remain outside that approval.

## Publication boundary

The target repository is public. The original local branch `codex/dev-147-m2-dp-altmode` has 14 unpublished task commits, including a raw private Linear export. Publishing that history would expose the export even if a later commit deleted it.

A new branch, `codex/dev-147-m2-dp-altmode-public`, starts at verified public base `7e5f80b18cfd788414a8c0373bfbfacc66c1449d`. The original branch and history remain unchanged. No force-push or history rewrite is required. The public checkpoint contains the 24 current task files other than the raw Linear export, plus the previously private authored D1/R4 sources and fixtures under [usbdiag](../../dev/apple-dp-altmode/usbdiag/README.md).

Public-only changes:

- Replace the real root-filesystem UUID and EFI partition UUID with invalid `LOCAL_ONLY_*` constants. Update the corresponding source-fixture expectation, without weakening the private guards.
- Replace the R4 launcher's private BASE/STAGE paths with invalid fixed paths. No environment override or generic fallback is added. Its host manifest is not published.
- Replace actual boot IDs with descriptive redacted labels. Keep synthetic fixture IDs, technical hashes, upstream commit IDs, and license/author attribution.
- Replace private absolute evidence links with explicit private-record labels. Use relative links where the exported source exists. Remove the public link to the excluded raw Linear export.
- Label dated records as public archival copies. Their recorded hashes and historical QA refer to the private originals, not edited public helpers. Preserve failures, corrections, successful trials, and open acceptance gates.

Raw Linear/device logs, manifests, package archives, module/image binaries, EFI files, and backups are excluded. Public helpers must not run live. The original operational helpers and both timestamped recovery backups remain private and unchanged.

## Fresh private continuation and RED runs

The parent prepared a new private D1 continuation. Only the sandbox BASE location changed from reviewed R4 source; the protection policy and manifest stayed fixed. The actual R4-equivalent probe passed once in `run-tutc5jn0`: wrapper exit 0, inputs preserved, empty stderr, seven smoke tests. The earlier 60-file D1 and 34-file R4 seals passed. All 15 readable system/prototype/recovery pins still matched.

The parent then ran the original frozen stubs, each after the actual isolation probe:

| Run | Result | Interpretation |
|---|---|---|
| Trace fixtures, `run-48sknd7o` | 32 tests; 40 errors; all NotImplementedError; exit 1 | Expected RED from the unimplemented validator. |
| Image fixtures, `run-p9o7z47r` | 16 tests; 30 errors; all NotImplementedError; exit 1 | Expected RED from the unimplemented image helper. |

Both sandbox results report `inputs_unchanged: true` and `timed_out: false`. The run directories and exact command/results remain private. These are initial RED observations, not a regression waiver or a successful implementation test. No compiler, archive/index control, diagnostic module, or image build ran in this checkpoint.

These fresh checks do not replace [R4's historical result](dev-147-sandbox-r4-2026-08-28.md), recover the earlier unknown errno, or validate the public launcher. The [D1 hold record](dev-147-usbdiag-d1-hold-2026-08-28.md) retains all three earlier failures. Historical evidence is not rewritten as a pass.

## Pending checks and next boundary

The parent independently checked the outgoing 39-file allowlist and the public-copy changes. The scoped credential/real-UUID scan and private-link/export-reference scan found no matches. No raw export or old private history is included. This is a scoped publication check, not a guarantee about excluded private records.

A frozen 40-file QA input set contains the 39 outgoing paths plus the unchanged shared Bash test base. In the actual reviewed sandbox, `run-6z34akxf` passed syntax checks for nine Bash/config files, eight Python files, and one JSON schema. The sandbox returned exit 0, unchanged inputs, no timeout, and empty stderr. These checks do not compile C, validate schema semantics, run the legacy functional fixtures, or test hardware. Literal unified-patch context whitespace remains unchanged; the separate non-patch whitespace check is the applicable publication check.

The legacy Bash fixtures need a mount view and tools absent from this strict sandbox. Its private `/tmp` also differs from their tmpfs assumption. Do not weaken isolation or claim those fixtures reran. The earlier aggregate suite still has five known failures, including the unsafe credentials-writing fixture; do not rerun it unrestricted. Python lint/type-check tools remain unavailable and are not reported as passing.

One initial read-only seal check used the wrong working directory, so relative seal entries did not resolve. The failure is retained privately. Rechecking each seal from its own root passed for all 60 D1 and 34 R4 files; this was a command correction, not an artifact repair or a build retry.

Next, finish the reviewed source checkpoint, then implement the trace and image helpers, run isolated GREEN/negative cases, review kernel control-flow preservation and log bounds, authenticate build inputs, and build private controls before diagnostics. Keep fresh outputs separate from sealed evidence. No boot staging, live load, cable test, or reboot follows from a source checkpoint. Full Gate 4b remains HOLD; Gates 5 and 6 remain open.

Rollback for this work is to leave the source and private outputs unused. No live system change needs reversal. Preserve the old branch, sealed evidence, working DP image/core, operational helpers, both boot backups, and macOS recovery bundle. Actual macOS restore execution remains untested.

## Publication outcome — later on 2026-08-28

The first checkpoint was committed as `c781312d1221da675e686b318a30ddd10d9ef3c4` and pushed to `origin/codex/dev-147-m2-dp-altmode-public`. `git ls-remote` returned the same hash. The outgoing history had exactly one new commit above the verified public base. The excluded raw Linear blob was not reachable through that outgoing history. No private branch, tag, release branch, or pull request was published.

The first push failed because Git's stored credential helper named an absent older GitHub CLI binary. A command-scoped helper used the current CLI, signed in as the repository owner, and the push passed. No global Git setting or credential was edited or disclosed. Further pushes must use the verified scoped helper until that separate configuration issue is fixed.

The non-patch whitespace check passed. All three literal patch payloads remain byte-identical to their private source copies. The public branch was clean after the push. The earlier pre-publication status above records its original cutoff; this section records the later outcome. Continue the approved offline D1 scope and push each completed source/evidence checkpoint. No boot action follows from publication.
