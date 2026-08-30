# DEV-147 — PR582 candidate startup, 2026-08-31

Host / scope: the M2 J413 machine, one attended boot after the accepted paired staging. Source checkpoint: `35f867ec8286cb264ace9d9177134333c757e9c3`.

## Result

David reports a working internal screen and responsive system after reboot. His initial wording, “external monitor now image”, was ambiguous. He then clarified that the external monitor does not recognize a connected device. This agrees with the captured lack of external video; it is not a startup PASS. He proposes replacing the LG 27 with the LG 35 after this check. That swap has not been confirmed.

The bounded, unprivileged startup snapshot was saved at 00:59:15 CEST. Loaded identities match the intended candidate:

| Check | Observed result |
|---|---|
| Kernel | `7.1.6-1-1-ARCH` |
| AppleDRM GNU build ID | `62b12eeb40983345a587cb46a168662817efe54a` — PR582 candidate |
| `tps6598x_core` GNU build ID | `40aa54382047ba36b02c9ac0da65a213862a77ad` — retained T1 core |
| Internal DRM connector | Connected, enabled; 2560×1664 mode available |
| External DRM connector | Disconnected, disabled; no modes |
| Compositor | Only eDP-1, 2560×1664 at 60 Hz; DPMS on |

These module notes establish the loaded target binaries. They are not a fresh whole-initramfs checksum. The unrelated `tps6598x` module note is not the core identity.

The saved journal contains 970 valid JSON records and 970 distinct cursors. All records match the before/after boot identity. Their monotonic timestamps span 1.837987–171.678022 seconds. Both journal and compositor commands exited 0 with empty stderr. Independent saved-file QA passed for capture integrity, module notes, display state and the 18 contiguous T1 markers. Raw identifiers and logs remain private. Kernel-journal SHA-256: `d7332b33d20706a9b0dec9f59b1108434c8459ea5523d7b40672409ef6327f33`.

## Startup interpretation

The T1 stream contains 18 records, sequence 1–18. Two role deferrals precede successful initialization. The cached state reports `plug=true`, `hpd=false`, `usb2=false` and `usb3=false`. The worker returns from its disconnected-HPD call and skips connected HPD with `reason=level_low`. Its USB mux and final role calls return 0.

The external DCP then boots and reports `connected:0 valid_mode:0 nr_modes:0`. Earlier probe deferrals are not treated as permanent failures. The internal display modesets successfully. No clear-swap timeout, crash report, kernel BUG/panic or DART/IOMMU fault was found in this saved interval. This is a bounded log observation, not proof that every silent branch was unexecuted or that the current crash flag is zero. Known firmware diagnostics and out-of-tree module taint remain.

The immediate observed blocker is a low HPD state with no external modes, before an external modeset. Why HPD stays low is unresolved. This does not demonstrate success or failure of PR582's later poweroff-timeout recovery change. The earlier crashed=1 observation belongs to the previous boot.

## Checks and containment

Reads used `uname`, bounded GNU module-note and DRM-attribute reads, `hyprctl -j monitors all`, and `journalctl -b 0 -k --no-pager -o json`. Compositor and journal reads had deadlines; the journal capture also had a file-size limit. `jq`, `cmp` and `sha256sum` checked saved files. No old helper or test suite was replayed.

No agent ran sudo, a probe, module operation, mode request, reboot or sysfs write. The unsafe partner `usb_mode` attribute was not read. No boot file, runtime configuration, image or recovery backup was changed. The candidate-boot handoff is consumed; this record grants no second boot or staging retry.

## Next boundary

The startup baseline is preserved. David's proposed one LG 27 → LG 35 swap is a separate hotplug comparison, not part of this startup result. Keep the lid open, MagSafe attached, the same lower/front port and empty monitor USB ports. Use the same physical USB-C cable if possible; record a cable change as a confounder. Wait about 10 seconds, then report external image, internal-screen health and responsiveness. Do not repeat reconnects or change modes. Stop on internal-screen or system trouble.

The LG 35 result, relevant timeout/recovery evidence and a matched control remain open. USB data, sustained charging, sleep/reliability, permanent integration and upstream submission remain outside this case. No rollback action is needed for these read-only checks. Normal default/W still retain the prototype DTB; neither is full stock rollback.
