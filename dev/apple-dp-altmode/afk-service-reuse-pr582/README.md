# AFK reuse with PR582 timeout semantics

This directory composes the accepted AFK service-reuse prototype with the
poweroff timeout behavior from Asahi Linux pull request 582.

Apply these patches in order to the exact accepted Asahi source commit
`e2e1930a9595bffafad92cec2b5504525efb9cd4`:

1. `../afk-service-reuse/afk-service-reuse.patch`
2. `pr582-timeout.patch`

The second patch keeps the 50 ms wait and the immediate timeout return. It
replaces only the timeout-path `dcp->crashed = true` store with a warning. The
RTKit crash callback remains the only writer of `dcp->crashed`. The atomic
guard remains unchanged.

Francisco Vargas authored and tested the PR582 timeout semantics. The local
patch omits the upstream explanatory C block comment to comply with this
repository's source-comment rule. See `../pr582/pr582-upstream.patch` for the
original patch, attribution, and provenance record.

Run the retained RED and the full source contract:

```bash
python3 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test_combined_candidate.py \
  --source-root /home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux \
  --red-only

python3 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test_combined_candidate.py \
  --source-root /home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux
```

The first command must exit 1 because the AFK-only source still writes the
permanent crash flag on the poweroff timeout. The second command applies both
patches in a temporary directory. It checks exact source identity, patch
scope, timeout control flow, the genuine crash writer, the atomic guard, and
negative mutations. It also runs the existing AFK lifecycle suite.

This candidate is not a default image or an upstream-ready patch series. It
does not authorize staging, loading, rebooting, cable changes, or boot changes.

## Authenticated image publication

`stage-image.py` publishes only the exact 21,599,177-byte combined image with SHA-256 `3207dd0ff346765f4514b34a137c1c7456c459082463355e51047216dedc2867` to the new non-default path `/boot/initramfs-linux-asahi-m2-displayport-afk-pr582.img`. It refuses an existing destination and preserves the default image, boot selection, `boot.bin`, GRUB, packages, modules, accepted candidates, format-2 rollback state, and recovery assets.

`stage-image-bootstrap.txt` is the literal root handoff. It embeds the publisher, writes it into a fresh root-owned mode-0700 transaction, authenticates its protected mode, size, and hash, then executes only that root-owned copy in an empty environment. The publisher requires root ownership for every ancestor of every protected, system, destination, transaction, and recovery path. Only the exact UID-1001 source path can have user-owned ancestry. It opens that source by file descriptor, verifies it before and after the copy, publishes without replacement, verifies the destination, rechecks every protected identity before commit, syncs the records, and changes `INCOMPLETE` to `COMPLETE` only at the final commit point.

Run the focused gate without privilege:

```bash
python3.14 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test-stage-image.py
```

The exact publisher, 26-test gate, and literal handoff passed independent functional QA and final adversarial security review. The destination was absent at review time. A separate manual staging handoff is the next action. Do not run the literal handoff with sudo until that handoff. Sudo, staging, reboot, and cable actions remain held. Any result other than the exact staging PASS requires inspection of the retained transaction. This includes a signal delivered after the durable commit point, where `COMPLETE` can exist even if the terminal reports a non-PASS result. Do not retry, select, or boot the candidate until that transaction is reviewed.
