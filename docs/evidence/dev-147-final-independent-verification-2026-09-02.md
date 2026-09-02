# DEV-147 release independent verification — 2026-09-02

**Result:** PASS
**Scope:** The ten checkboxes completed after the earlier independent QA marker

This gate verifies the accepted release implementation and handoff. It does
not claim that the live legacy format-1 installation has migrated to format 2.

## Classification

- VERIFIED: 2
- DISPUTED: 0
- UNVERIFIABLE HERE: 8

The verifier directly confirmed Slices 4 and 5 from the repository, saved
evidence, test results, and remote state. The eight Slice 3 claims depend on
root-only state or physical actions. A fresh unprivileged verifier cannot
repeat those actions. They remain accepted with David's explicit command
output and physical-observation provenance. No saved evidence conflicts with
them.

## Repeated gates

- The focused M2 DisplayPort integration test passed.
- `bin/omarchy commands --check` passed for 454 commands.
- Parser-selective command syntax passed.
- Changed-script Bash syntax passed.
- `git diff --check` passed.
- The repository suite completed all 236 shell test files and exited 1 only
  for `config-test.sh`, `unowned-system-paths-test.sh`, and
  `zram-package-contract-test.sh`. These are the recorded unrelated package
  checkout or contract failures. No DEV-147 test failed.

The code check confirmed strict 16-field format-2 state, refusal of legacy
format-1 state, the root-owned mode-0700 checksummed rollback runner, separate
preparation and activation, the package guard, and boot-first rollback order.

## Remote state

The fork draft PR is open against `quattro-arm` at hardened commit
`b45948e129a5197d7174aa2c4c870134b03fdff6`. Omarchy Mac PR #289 remains open
against `quattro` with changes requested. No upstream submission was made.

## Migration boundary

The live installation still has format-1 state. The exact matching rollback
implementation is preserved in the detached worktree
`/home/david/o/.dev147-stage/dev147-format1-rollback-6dbcc24ad` at commit
`6dbcc24adbf7bfe435b1c64b0ec5c6ff5eed0f09`. Its integration script has
SHA-256 `6c93c39a97b8e0d42f5f2be262907759713e9718146f40a41e23ab4123c34a17`.
No boot file changed while this checkout was created and verified.
