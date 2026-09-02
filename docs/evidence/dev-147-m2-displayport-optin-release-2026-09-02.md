# DEV-147 M2 DisplayPort opt-in release evidence — 2026-09-02

**Host / scope:** `omarchy-air`, M2 MacBook Air J413, opt-in DisplayPort release candidate
**Approval:** proceed-and-report tier; Slice 4 was restricted to repository work without live changes
**Repo state:** `codex/dev-147-m2-displayport-opt-in`, based on `6dbcc24adbf7bfe435b1c64b0ec5c6ff5eed0f09`; Slice 4 commit pending at record time

## What happened

The integrated candidate booted as `/boot/initramfs-linux-asahi-m2-displayport.img` on boot `fa500274-a4fd-49e3-a84a-82ec4948b8e3`. Kernel `7.1.6-1-1-ARCH` loaded TIPD build ID `50ee94a5f8dbae780c676a73b611a7ad5197e47a`.

The accepted live matrix produced these results:

| Case | Result |
|---|---|
| Internal-only startup | Built-in panel normal and Linux responsive |
| LG 27UN83A-W attach | 3840×2160/59.997 Hz image after about five to six seconds |
| Same-boot LG27-to-LG35 switch | 3440×1440/99.982 Hz image after about five seconds |
| Post-switch internal panel | Physically normal and Linux responsive |
| Autonomous link reset | External video recovered in about 9.6 seconds; the monitor USB hub did not return |
| Attached-display suspend | Unsupported after the recorded resume failure |

The USB hub result belongs to [DEV-163](https://linear.app/helmus/issue/DEV-163/lg-monitor-usb-hub-disappears-while-displayport-video-remains-active). A live monitor switch can leave the exported EDID and Hyprland monitor identity stale even when native video works.

The accepted boot retained `disablehooks=encrypt`. This unrelated argument qualifies the live result. It is not part of the feature and must not be added to the boot instructions.

Slice 4 preserved the exact reviewed integration script as root-owned `/var/lib/omarchy/m2-displayport/active/rollback.sh` during preparation. State format 2 contains 16 strict fields, including the preserved entrypoint SHA-256 and size. Activation and rollback reject checksum, ownership, or mode drift. The regression test changes and removes the source copy before it runs rollback from the preserved entrypoint.

No `sudo`, reboot, cable action, package operation, boot-file write, or other live-system change occurred in Slice 4.

## Result

The focused integration test returned `VERDICT: PASS`. Command metadata, Bash syntax, local documentation links, and `git diff --check` passed. `bin/omarchy commands --check` validated all 454 commands.

The first fresh `./test/all` run exited 1 for four unrelated failures.
`config-test.sh` and `unowned-system-paths-test.sh` were missing-checkout
environment failures and passed with a disposable `omarchy-pkgs` checkout.
`zram-package-contract-test.sh` was a separate pre-existing
dependency-contract failure that persisted with that checkout.
`emojis-test.sh` showed an unrelated flaky transient-clipboard race, with one
failure in 20 isolated reruns after mixed results.

Boundary QA repeated the complete gate after the final evidence file was added.
The aggregate run finished in about 142 seconds and failed only the three
package-related tests. The emoji test passed in that aggregate run and in 20 of
20 isolated reruns. The focused DEV-147 test passed. Fresh QA therefore found
no DEV-147-specific failure but returned `VERDICT: FAIL` because the aggregate
gate remains red for the three unrelated package cases.

Fresh review passed after the checkout-independent rollback fix. Review
retained one migration boundary: the current live installation still has
format 1 state and no preserved rollback entrypoint.

## Rollback

New format 2 preparations use:

```bash
sudo /usr/bin/bash /var/lib/omarchy/m2-displayport/active/rollback.sh rollback
```

The current live format 1 installation must first use the exact integration implementation from commit `6dbcc24adbf7bfe435b1c64b0ec5c6ff5eed0f09`:

```bash
sudo /usr/bin/bash /absolute/path/to/6dbcc24ad-worktree/dev/apple-dp-altmode/m2-j413/integration.sh rollback
```

Only after that rollback passes can a fresh format 2 preparation replace the legacy state. Do not use the newer integration script to roll back format 1 state.

## Open

- Run the legacy rollback and a fresh format 2 preparation only as a separate attended live operation.
- Keep attached-display suspend unsupported.
- Keep monitor USB data in DEV-163.
- Treat hot-switch EDID and Hyprland identity as potentially stale.
- A boot without `disablehooks=encrypt` remains necessary for an unqualified production-argument result.
