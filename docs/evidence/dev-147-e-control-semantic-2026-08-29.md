# DEV-147 E-control semantic and zero-child regression checkpoint

Date: 2026-08-29

This record accepts the fixed E raw-observation semantic boundary. It does not accept the later real E control or T1 image. All work used the unprivileged offline sandbox. No live driver, device, boot, staging, sudo, cable, recovery, or hardware action occurred.

## Containment

The first resumed probe stopped because the pinned v4 runtime named the replaced `/usr/lib/libgcrypt.so.20.7.2`. Package integrity was clean. A new immutable v5 manifest changed only that one source to `/usr/lib/libgcrypt.so.20.8.8`. The v5 manifest has 582 entries and SHA-256 `5886d68d263c773990f2c7c5675f63e05debf5c78cdf693440339fddfca947c0`. A fresh v5 probe passed. The v4 manifest and drift-stop record remain preserved.

Every accepted run used UID/GID 1001, empty capabilities, no network, no visible host `/proc`, `/sys`, `/run`, `/home`, or `/boot`, read-only inputs, and only `/work` and `/tmp` as writable storage. Input fingerprints stayed unchanged.

## Semantic RED and GREEN

The accepted replacement RED is `run-nqnr8soj`. Setup passed. It produced exactly the three specified assertion failures, with zero errors, skips, or workload children. It retained 424 complete JSON/stdout/stderr fixture triplets and produced no pending, fixture-final, or real E result. The reviewed aggregate candidate was `68dd45eeeb9239b873c293b81cbbb5b7403d4ff0d5d1b5a32f3e27c14c92d44e`.

Two later GREEN attempts stayed fail-closed. `run-6swsqrwz` exposed an AST-runner field error and exited 2. `run-flf195ba` exposed a publication-helper source-shape error and exited 1. Neither ran a workload child or produced a real E result.

The accepted GREEN is `run-vfbn_07m`:

- 3 tests passed with zero failures, errors, or skips.
- 606 read-only mounts remained unchanged.
- All 424 fixture reports were `FIXTURE_ONLY`, `executed=false`, with null PID and return code.
- The sole result was `NONFRESH_FIXTURE` with the aggregate above.
- Structural, operational, fresh, image, load, stage, and boot fields were false.
- No pending file or real E result existed.

The accepted subject SHA-256 is `70f369f87942b6ca6826c808536353ae0cc400123204040b9c005995ab43c3e3`. The semantic runner SHA-256 is `4c14f023d719dd4e709e424812d53f96ab535fdeb7de2461e5b1c63a813099b2`.

Independent QA and safety review passed the retained run and the no-replace publication path. The real operational APIs remained closed.

## Regression gates

The first two structural reruns stopped at stale private-snapshot mode assumptions. `run-urf729h4` rejected the current runner mode. `run-b_gwjn23` then rejected the current subject mode. Both exited 2 before setup, kept inputs unchanged, and left only isolation logs and sentinels. The runner now requires repository-normal mode `0644` for its own test file and the exact `/inputs/recipe` subject. Every other pinned private source/base input still requires `0600`; all type, ownership, link, size, hash, and before/open/after identity checks remain.

The accepted structural regression is `run-f0tjlamv`:

- 3 tests passed with 594 unchanged read-only mounts.
- The eight bindings and fixed 424-command plan matched.
- All 1,272 structural files were present.
- Zero workload children ran.
- No real E result or operational output existed.
- The final structural result was absent after the deliberate refusal test, as specified.

The accepted pure recipe regression is `run-m64c0_of`:

- All 16 methods passed with 605 unchanged read-only mounts.
- The fixed E identity, 200-module model, seven original indexes, twelve historical fixture files, 1,408 alias mappings, 596 symbol mappings, and exact 424-command plan matched.
- Zero workload children ran.
- Operational and assembly gates remained closed.

Independent QA and safety review passed both regression runs. The current structural runner SHA-256 is `8816d63874b1590c24b5ac468d38a644896836a6dc76dcc7df4aaf6b5d2b2c70`. The recipe runner SHA-256 is `ab7e297f9b80f787a8137876df4d056208e2b74d237db71e2aefba3f7c3e956f`.

## Boundary and next gate

This checkpoint proves complete semantic validation of nonfresh fixture observations and preserves the zero-child structural and pure-recipe boundaries. It does not prove fresh depmod, gzip, archive-tool, lookup, image, module, startup, USB, charging, or display behavior.

The next A2 gate is a separate real E no-change/index control. It needs a new zero-child execution RED, exact eight-input isolated launch contract, implementation, focused GREEN, and independent pre-execution review before one fixed 424-child sandbox run. No workload run is authorized by this record alone. T1 assembly follows only after that complete proof is accepted.
