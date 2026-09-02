# DEV-147 AFK reuse staging readiness

**Date:** 2026-09-02
**Approval:** David approved the recommended root-owned authenticated staging path.
**Scope:** Offline staging implementation and review only

## Safety correction

The first wrapper hashed a user-owned shell library and then sourced the same pathname as root. Independent review rejected it because another same-user process could replace the file between those operations. The rejected wrapper was removed. It never ran on the live system.

The replacement is a literal command in `dev/apple-dp-altmode/afk-service-reuse/stage-image-bootstrap.txt`. It starts with `/usr/bin/sudo` and an empty environment. The literal creates a new root-owned mode-0700 transaction on `/boot`. It writes the embedded publisher exclusively as root-owned mode 0500 data, verifies those destination bytes, syncs them, and only then starts `/usr/bin/python3.14 -I -S -B` on that authenticated file.

The publisher keeps an `INCOMPLETE` marker until the exact candidate is durable and every final host and protected-path check passes. It publishes with an atomic no-replace hard link, syncs the destination directory, removes the temporary name, verifies the one-link destination by descriptor, and atomically renames `INCOMPLETE` to `COMPLETE` as the commit point. Failures before commit remove only the matching candidate inode and retain `INCOMPLETE`. Neither path changes boot selection.

## Identities

- Publisher SHA-256: `40c4acd8868270c94f7805d6e11a60765abe7546305d349e0a5db4fbcb4d6906`
- Publisher size: 28,236 bytes
- Bootstrap SHA-256: `a21b8e54f2b8e31c4d0d7fbba16d94a1a7a55226b2b509cdd677e51d363f8e3d`
- Test SHA-256: `602c0d128f4a2cb8fa8a131be7eca18fdf8e030cd1a8191d5e47b026a8418c34`
- Candidate SHA-256: `ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd`
- Candidate size: 21,598,988 bytes
- Candidate metadata: UID 1001, GID 1001, mode 0600, one link

## Validation

The focused command was:

```bash
python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse/test-stage-image.py
```

It passed 20 of 20 tests. The tests include the rejected hash-then-source design, the exact embedded payload, the actual production candidate copy, mutable source and protected-file descriptor changes, protected leaf and ancestor pathname replacements, destination collisions and symlinks, candidate metadata and hash refusal, fresh fact and mount drift, every publication and completion fault boundary, signal cleanup, coherent markers, protected boot snapshots, and exact bwrap bootstrap tamper and collision controls.

Python AST, bootstrap Bash syntax, no-code-comments, unprivileged root refusal, candidate before/after identity, payload equality, and `git diff --check` passed. The command metadata gate passed 455 commands. Entrypoint parser checks passed 5 Python and 453 Bash files.

The final repository boundary aggregate completed 235 test files. DEV-147 passed. Three unrelated package-ownership tests failed because this isolated worktree has no `omarchy-pkgs` checkout: `config-test.sh`, `unowned-system-paths-test.sh`, and `zram-package-contract-test.sh`. The earlier transient live Quickshell failure did not recur. Command metadata passed 455 commands. Entrypoint syntax passed 5 Python and 453 Bash files.

Independent QA reported `VERDICT: PASS`. Final security review reproduced the protected ancestor replacement attack against the earlier revision, verified that the final revision rejects it with `protected pin canonical path changed`, and reported `REVIEW: PASS` with no exploitable or boot-unsafe blocker.

Fresh-context milestone verification reported `PASS` with zero disputed claims and no item to reopen. It reran the exact lifecycle and 20-test staging gates. It independently ran the protected ancestor replacement and real production-candidate copy tests. It verified 39 local links across five documents, command metadata for 455 commands, syntax for 5 Python and 453 Bash entrypoints, and the three staging artifact hashes. Historical negative-action and root-private state claims were not re-creatable from an unprivileged checkout. The plan accepts them with David's explicit approval and prior command or physical provenance. The later full boundary aggregate supplies the final three-failure result above.

## Live state and rollback

No `sudo`, staging, `/boot` write, package operation, module action, reboot, or cable action occurred during this work. `/boot/initramfs-linux-asahi-m2-displayport-afk-reuse.img` remains absent. No matching `/boot/.dev147-afk-reuse-stage.*` transaction exists.

The accepted display image, normal image, `boot.bin`, GRUB configuration, packages, loaded modules, source candidate, and boot selection remain unchanged. The new candidate is non-default. Before a successful candidate boot, rollback is to select the accepted `/boot/initramfs-linux-asahi-m2-displayport.img` image. Image removal is optional and must follow the retained transaction's exact hash-bound `REMOVE.txt` instruction.

## Open gate

David must paste the reviewed literal into a terminal. A successful run must print `AFK REUSE IMAGE STAGING PASS` and retain a `COMPLETE` transaction. Stop after any other result. Reboot and the ten-generation display test remain separate attended actions.
