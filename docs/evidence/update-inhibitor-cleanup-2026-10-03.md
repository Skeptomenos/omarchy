# Update inhibitor cleanup investigation

Recorded on 2026-10-03 against base `6214d3666`, in the `fix/update-inhibitor-cleanup` worktree. Scope was the update helper and regression coverage. No privileged command, package upgrade, live-checkout edit, commit, or push was performed.

## Incident and diagnosis

The local `/tmp/omarchy-update.log`, lines 6223–6243, records eleven completed mise upgrades, then `Failed to stop the Omarchy update sleep inhibitor.`, followed by update exit status 1 at 11:09:36 CEST. This was a cleanup failure, not a failure of those tool upgrades.

At the base revision, `bin/omarchy-update-stay-awake` records the PID and start time of the launched privilege wrapper. Stop sends TERM to that PID, suppresses any signal error, and polls for only fifty 20 ms intervals. The existing tests replace both privilege wrappers with `exec`, which removes the wrapper lifetime from the fixture.

The installed `sudo(8)` manual, version 1.9.17p2, describes a separate command process, an optional pty monitor, and policy/PAM closure before sudo exits. The matching [sudo 1.9.17p2 source](https://github.com/sudo-project/sudo/blob/v1.9.17p2/src/exec.c#L521-L550) has a two-second interval between TERM and KILL in `terminate_command`. This interval applies to termination paths, not every normal TERM delivery. It establishes that a one-second wrapper deadline is not generally sufficient.

The new `test/shell.d/update-inhibitor-test.sh` retains a wrapper and its child. It models delayed TERM teardown and post-command wrapper closure. Before the implementation change, `bash test/shell.d/update-inhibitor-test.sh` exited 1 with the incident's exact cleanup error. After the change, it passes without an EXIT retry. A denied-signal fixture also passes without invoking `kill`.

The original wrapper process and its signal result were not captured. The exact incident path, delayed teardown versus insufficient signal permission, is not recorded. The timing defect is reproduced; a specific original sudo/PAM delay or permission failure remains an inference.

## Change

- Create a mode-600 FIFO inside a mode-700 helper-state directory. Open it before forking so an immediate stop request cannot precede the reader's descriptor.
- Run `systemd-inhibit` with `bash -c 'read -r'` instead of `sleep infinity`. Stop writes one newline through the pipe. The inhibited command exits normally, then the privilege wrapper closes its session.
- Keep the PID/start-time guard before any stop request. Remove the pipe with the helper state only after successful cleanup or stale-PID detection.
- Wait up to 250 polling intervals of 20 ms for wrapper exit. Keep the signal fallback for state created by older versions.
- Close the inherited update-lock descriptor before the wrapper starts. The regression inspects both wrapper and child descriptors.
- Keep existing Stay Awake ownership checks. Tests cover pre-existing state, a newer user choice, and PID reuse, including no write to a stale control pipe.

## Verification

- Before the fix, `bash test/shell.d/update-inhibitor-test.sh`: exit 1, `Failed to stop the Omarchy update sleep inhibitor.`
- After the fix, `bash test/shell.d/update-inhibitor-test.sh`: exit 0, four assertions passed. Covers retained wrapper/child, denied signalling, immediate stop before child startup, terminal sudo wrapper, and legacy state with teardown beyond one second.
- `bash test/shell.d/update-lock-test.sh`: exit 0, seven assertions passed.
- `bash test/shell.d/update-sequence-test.sh`: exit 0, twelve assertions passed.
- `bin/omarchy commands --check`: exit 0, 488 commands passed.
- Shebang-aware syntax check of every `bin/omarchy-*`: exit 0. Bash files used `bash -n`; Python files used `ast.parse`.
- `git diff --check`: exit 0.
- `shellcheck --shell=bash -S error bin/omarchy-update-stay-awake`: unavailable, exit 127 because shellcheck is not installed.
- First `./test/all` attempt exceeded the 120-second tool timeout. A longer background run was started; its result is pending at this recording.

## Limits and handoff

Tests use nonprivileged wrapper fixtures, not real sudo, Polkit authentication, or logind inhibition. A user-run update or disposable-machine rehearsal is still needed to prove the privileged path. Stop does not request authentication. Authentication at start remains unchanged. A wrapper that never starts or never exits still causes a bounded cleanup failure and retains its PID/pipe state for a retry. Old state without a pipe still needs signal permission.

The SWE change is ready for independent QA and review. It is not a release or a live deployment.

— drafted by David Helmus's agent

## Verification addendum, 2026-10-03

The background `./test/all` run completed with exit 1. CLI passed. Shell reported 10 failures among 341 files. The failing files were `arm-channel-staging-test.sh`, `config-test.sh`, `factory-reset-accounts-test.sh`, `legacy-power-udev-rules-migration-test.sh`, `locate-test.sh`, `network-package-test.sh`, `package-build-contract-test.sh`, `settings-package-units-test.sh`, `unowned-system-paths-test.sh`, and `zram-package-contract-test.sh`.

Reported blockers were a tmpfs cache fixture, missing or unversioned omarchy-pkgs recipes, an unset `OMARCHY_PATH` in two tests, and a UTF-8 decode error in locate coverage. These failures are outside the changed helper's focused tests. A full-suite baseline comparison was not run, so they are not claimed as proven pre-existing failures. Full output is in `/tmp/opencode/update-inhibitor-all-final.log` on this host. QA should rerun with `OMARCHY_PATH` set to the checkout and the required package recipes available.

After that suite started, coverage was extended to an unresponsive inhibitor. The final `bash test/shell.d/update-inhibitor-test.sh` run exited 0 with five passing cases. The extra case proves that cleanup failure stays visible, retains the PID and pipe for a retry, and removes them after the child exits. This supersedes the four-case result above. The updated lock and sequence suites also passed individually.

## Review correction and live verification addendum, 2026-10-03

Review found that the wrapper fixture launched its child with `"$@" &`. Noninteractive Bash redirects background stdin to `/dev/null` unless the command redirects it explicitly. The read child could therefore exit before stop. Earlier passing results did not prove that stop reached a live reader. This correction supersedes the retained-reader claims in the earlier verification records.

The fixture now launches `"$@" <&0 &`. Before stop, the ordinary retained-child, terminal-sudo, and unresponsive-child cases assert that the child is live, is not a zombie, and has fd 0 open on the helper's control FIFO. The delayed-start case clears stale markers, asserts that no child has started yet, and checks that the wrapper already holds that FIFO on fd 0 before sending stop. No production code changed in this review round.

Corrected focused runs:

- `bash test/shell.d/update-inhibitor-test.sh`: exit 0, five cases passed.
- `bash test/shell.d/update-lock-test.sh`: exit 0, seven assertions passed.
- `bash test/shell.d/update-sequence-test.sh`: exit 0, twelve assertions passed.
- `bash -n test/shell.d/update-inhibitor-test.sh`: exit 0.
- `git diff --check`: exit 0.
- Negative sensitivity check: piped an in-memory copy of the corrected test to Bash with only the explicit child stdin redirection removed and the base-test source path made absolute. It exited 1 with `not ok - inhibitor child is alive before stop`. This confirms that the new assertions reject the original fixture defect. No repository file was changed for that check.

David reported running `bash /tmp/opencode/verify-update-inhibitor.sh` and selected `Both PASS lines`. This is user-reported semantic verification, not execution or output directly observed by this SWE session. The script was read directly. It runs the patched checkout helper under the real update lock, checks `systemd-inhibit --list` before and after stop, and prints `PASS: real update inhibitor acquired` and `PASS: real update inhibitor released without a cleanup error`. The report supports acquisition and release on the real sudo/logind path. It does not establish every Polkit or failure path, or the original incident's kill reason.

The host journal was read directly with `journalctl _PID=8320 --since '2026-10-03 11:05:00' --until '2026-10-03 11:10:00' --no-pager -o short-precise`. It records the original sudo command running `systemd-inhibit --what=sleep:idle --who=omarchy-update --why="Omarchy update in progress" --mode=block sleep infinity` at 11:05:47.462909 CEST. It records PAM session closure at 11:09:36.840956 CEST. The journal establishes command startup and later session closure, not the exact signal, permission result, or reason the original one-second stop deadline was exceeded.

No commit or push was made. Independent QA and review remain the release gate.
## Release approval addendum, 2026-10-03

Independent review passed after the wrapper fixture correction. Independent QA ran `OMARCHY_PATH="$PWD" ./test/shell` synchronously on both the fixed checkout and clean baseline `6214d3666`. The fixed checkout failed 8 of 341 files. The baseline failed the same 8 of 340 files. Comparing failed-file lists returned exit 0. No new failure was introduced.

The common failures were `arm-channel-staging-test.sh`, `config-test.sh`, `locate-test.sh`, `network-package-test.sh`, `package-build-contract-test.sh`, `settings-package-units-test.sh`, `unowned-system-paths-test.sh`, and `zram-package-contract-test.sh`. Logs are `/tmp/opencode/qa-corrected-fixed-shell.log` and `/tmp/opencode/qa-corrected-baseline-shell.log` on this host.

The corrected focused suites passed with 5 inhibitor scenarios, 7 update-lock assertions, and 12 sequence assertions. `./test/cli` passed 119 assertions. Command metadata passed for 488 commands. Syntax and diff checks passed. Hyprland reload was not required for this script-only change and the agent shell had no compositor connection. Shellcheck was unavailable. Actual Polkit behavior remains unverified.

David selected "Waive and release" after reviewing the eight unchanged baseline failures. This explicitly waives those failures for this fix only and authorizes committing and pushing to `origin/quattro-arm`. David must run `omarchy update` from his terminal to deploy through the normal release path. This record is release approval, not proof of live deployment.
