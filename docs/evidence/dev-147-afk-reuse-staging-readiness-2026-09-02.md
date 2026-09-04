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

## 2026-09-03 default-image pin correction

The first live use of the 2026-09-02 literal safely reported `REFUSED: protected pin mismatch: /boot/initramfs-linux-asahi.img` before candidate publication. The candidate destination remained absent. Do not rerun that superseded literal.

The publisher carried the pre-AVD default-image SHA-256 `625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296`. David's privileged read reports that the current root-private `/boot/initramfs-linux-asahi.img` instead has SHA-256 `c4cffb397cfbd0158d3b1423c0512e1622053d53e0c75a17f5312986276324e0`. Its 18,865,707-byte size and 2026-08-31 modification time match the documented DEV-162 Apple AVD firmware rebuild.

The corrected publisher pins the post-AVD hash. A production-config regression test requires that hash and rejects the old value. No other production pin changed. The kernel patch, candidate module, candidate image, source image, and live state did not change.

Corrected identities:

- Publisher SHA-256: `64bbd13d2d8199257c2664c1baa10d42dd9333bb9e0f0bfc5d86de2ff1bd6d82`
- Publisher size: 28,236 bytes
- Bootstrap SHA-256: `ffb9ad2f6dfd22d104d7fb03d453d3ef2f060562776592c50ffebe3a89997bc5`
- Test SHA-256: `b161a185f6b1e652837dc5c8109ad354bf38f8172665cfe6af1ce9a92b9650d2`
- Candidate SHA-256: `ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd`
- Candidate size: 21,598,988 bytes

`python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse/test-stage-image.py` passed 21 of 21 tests. Python AST, bootstrap Bash syntax, embedded-payload equality, source and bootstrap hash binding, `git diff --check`, and the candidate/source scope check passed. Independent QA and final security review pass. The old root-owned `INCOMPLETE` transaction cannot collide with a new random transaction or overwrite the fixed destination. Final repository checks pass for 455 command metadata records and 458 command entrypoints. `./test/all` completed all 235 shell files and retained only the three known unrelated failures caused by the absent `omarchy-pkgs` checkout.

## 2026-09-04 complete root-only baseline correction

The replacement live run passed the corrected post-AVD default-image pin and safely reported `REFUSED: protected pin mismatch: /boot/grub/grub.cfg` before candidate publication. The publisher still carried GRUB SHA-256 `68c36bbbb3c530dba8647f9435252da53adf53942b37b76e399ccd234cc0f24d` from Gate 0. The current 4,129-byte GRUB file was intentionally regenerated during the documented 2026-09-01 persistent boot-cleanup adoption. The candidate destination remained absent. Two root-owned `INCOMPLETE` transactions retain the failed runs.

The self-correction stop rule blocked another one-pin retry. David then supplied one privileged SHA-256 read of every root-only protected file:

- Accepted display image: `a93dd0c1b3a6c4d81bf76f2f43c7c7a2b8b7e1e0306bc487de018667f9c8c196`
- Post-DEV-162 default image: `c4cffb397cfbd0158d3b1423c0512e1622053d53e0c75a17f5312986276324e0`
- Post-cleanup GRUB configuration: `57d839b9bc7d3488402a8cf7c9e45328dc0097731fc395b0514c467d06b7a327`

The accepted and default image hashes match the existing publisher. Only the GRUB pin changed. The regression now requires all three exact current hashes. It also rejects the pre-AVD default hash `625641095075a9a2396bc701ffd48ac58f2c8a1758e250fa3f6b55b29dcae296` and pre-cleanup GRUB hash `68c36bbbb3c530dba8647f9435252da53adf53942b37b76e399ccd234cc0f24d`.

Current corrected identities:

- Publisher SHA-256: `2bb70432f43f9ac678cd4498ed034c528305b5ef943e17a960cb39174037a48d`
- Publisher size: 28,236 bytes
- Bootstrap SHA-256: `1f762b213dc0b7218835e4f6c36e8db8276308bb8b7b9c3f088d274226feae73`
- Test SHA-256: `4b216c21bc02888a4a70a7b541844331a4477f27f26dfc5cbbd9980c2a1ac633`
- Candidate SHA-256: `ebd383c21a35d6b0eff22ffe6f144ea7790c31d7cf058a1c3afa5e39c2375acd`
- Candidate size: 21,598,988 bytes

`python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse/test-stage-image.py` passed 21 of 21 tests. The strengthened baseline test failed on the superseded GRUB hash before the publisher change and passed after it. Independent QA reran the 21-test gate, Python AST, bootstrap syntax, exact embedded publisher hash and 28,236-byte size, `git diff --check`, 455 command metadata records, and all entrypoints: 5 Python and 453 Bash. `./test/all` completed 235 files and retained only the same three unrelated failures caused by the absent `omarchy-pkgs` checkout. Adversarial security review reported PASS with no bugs or suggestions. This correction did not stage an image or change `/boot`, boot selection, packages, loaded modules, cables, or the running system. The corrected literal is ready for one separate user-run staging attempt. Staging, reboot, and hardware validation remain pending.
