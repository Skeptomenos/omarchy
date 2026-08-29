# DEV-147 E execution boundary evidence — 2026-08-29

**Scope:** Contained, unprivileged offline A2 execution-boundary work only.
**Result:** The exact zero-child RED and corrected GREEN passed their gates. No real E-control workload ran.

## Holds

Candidate-image creation, assembly, staging, sudo, reboot, cable action, device access, module load, boot-file access, live testing, and recovery rehearsal remained on HOLD. The sandbox exposed no host `/proc`, `/sys`, `/run`, `/boot`, `/home`, `/root`, or network route. Only `/work` and `/tmp` were writable. All retained runs used 594 read-only test bindings. The fixed production model remains eight task inputs and 593 read-only bindings.

## Retained sequence

| Checkpoint | Subject / runner SHA-256 | Result |
|---|---|---|
| Controlled RED, `run-0zk61la1` | Subject `70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3`; runner `190cad41fcec6f3c6797087e8466b813d21ba3b0cd0c12d01d370a07c85b6fec` | Exit 1. Setup passed. The exact three selected methods produced three assertion failures, zero errors, and zero skips. They stopped at the missing fixed-source bootstrap, execution policy, and bounded collector boundaries. |
| First GREEN stop, `run-_l2w9p_k` | Subject `cf6eca34c7c0303249fcc4249dc358252ca335d5d0e9f4c0561ec80c1a3a7097`; runner `398d2628e94ff60e201635702394eacf59b94d5a11badcc78be5f04b20cbfdfe` | Exit 2. Setup and the first two methods passed. The collector method stopped before its synthetic collector fixtures because Python 3.14 returns `PosixPath` from `Path(...)`, which made the runner's `type(path) is Path` predicate false. The same impossible exact-type predicate existed in the authenticated tree-helper template. This is not accepted GREEN. |
| Corrected GREEN, `run-nr5woop4` | Subject `39496435f113c7d9256e5592effd3fece8c52b0e61b774e8283fe96eb84d4add`; runner `443ed64c1659422b4eca9527615b59ed7180bdebcd313ce76595ee2b23611ac1` | Exit 0. Setup passed. All three methods passed in 0.900 seconds, with zero failures, errors, or skips. The narrow correction used `isinstance(..., Path)` in the subject, authenticated template, and spy. Absolute-path and fixed-root checks stayed unchanged. |

Every run reported unchanged inputs and no timeout. Every run executed zero control-workload children. The RED and corrected GREEN planned 424 later children but did not start them. Searches found no operational child root, control root, lookup root, cpio stream, real result, candidate image, staging output, module-load result, or boot result. Synthetic GREEN fixtures stayed below `/work/e-control-execution-red`.

## Accepted boundary

The accepted 188-node subject matches all 44 complete future AST reference nodes. It now supplies:

- a fixed five-source, hash- and identity-authenticated bootstrap with full module rollback and Python-path restoration;
- one frozen eight-input execution policy for UID/GID 1001, `/work`, umask `077`, 593 read-only mounts, 424 planned children, and fixed time limits;
- no-follow bounded readers for 1,272 child records, two fixed trees, the empty configuration, and the two E streams.

The focused tests cover source identity, hash, mode, link, symlink, and size refusal; exact policy equality; exact collector wiring; record membership; tree membership, depth, per-file and aggregate caps; and input immutability. Independent QA and safety review passed before both GREEN attempts and accepted the narrow correction before the second run.

`operational_policy()`, `finalize_operational_result()`, and `main()` still raise `E_CONTROL_RECIPE_UNAVAILABLE` unconditionally. This checkpoint proves the fixed launch and collection boundary only. It does not prove fresh E reconstruction, a no-change operational control, T1 source or binary safety, image correctness, startup behavior, DisplayPort causality, USB behavior, or hardware success.

## Next gate

One separate independent pre-execution review is required before the fixed 424-child E no-change control may run in the same offline sandbox. That review must authenticate the accepted subject and runner, the exact eight inputs, 593-mount production model, child plan, result publication boundary, timeout/kill/reap behavior, and absence of any candidate-image or live path. A setup, containment, child, input, or result failure stops the gate. No staging or manual action follows automatically.
