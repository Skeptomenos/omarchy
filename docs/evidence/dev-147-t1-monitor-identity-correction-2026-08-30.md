# DEV-147 — T1 monitor and cable correction — 2026-08-30

**Scope:** Correct the physical setup attributed to the [T1 startup capture](dev-147-t1-boot-capture-2026-08-30.md). Preserve that record and its raw files unchanged.
**Source:** David's clarification after the capture and his subsequent cable clarification. The swaps below were user actions, not a new agent-run test.
**Repo state:** `b5e676555fe56845a96ecf7d6e1eee09fa422a45` before this correction.

## Corrected observations

| Case | User-reported result | Evidence limit |
|---|---|---|
| T1 startup with new LG 27-inch 4K monitor | No external image; internal screen normal and system responsive | This is the monitor used for the retained T1 capture, not the original monitor. |
| Original LG 35-inch widescreen reconnected | External image appears | Post-capture report only; no matching capture or independent identity check. This is not an original-monitor startup test. |
| New LG 27-inch 4K reconnected | No external image | Post-capture report only. Currently connected; original monitor disconnected. |
| New monitor and its cable on other devices | Works | User report. Other device, connection mode and display settings are unspecified. |

Each monitor used a different USB-C cable. Exact model numbers, cable specifications, identical Mac port, direct connection and unchanged boot during the swaps still need confirmation. The old monitor's earlier measured mode was 3440×1440 at 99.982 Hz; “2K” is David's description, not a new measurement.

The prior interpretation assumed the original monitor. That assumption was wrong. Record T1 startup failure for the new monitor/cable combination only. The reported original-monitor recovery is useful, but it is not yet a controlled monitor-only comparison. Working on another device lowers suspicion of a completely failed monitor or cable; it does not prove compatibility with this Mac's current DP path.

## What the existing capture can tell us

- The qualified T1 code identity, 1,106 journal envelopes, 39 diagnostic records and two connected-HPD call returns remain valid. The correction changes setup attribution, not those results.
- Saved external-DCP messages include connect activity and 28 `set_drive_settings` messages. The only saved external `dcp_hotplug()` report says disconnected, no valid mode and zero modes. No later connected report appears in this snapshot.
- There is no EDID or DPCD message text in the saved journal. This does not establish that EDID/DPCD was absent or unreadable on the device. No fresh connector or compositor state was collected.
- The numeric drive-setting fields are not decoded here. The messages alone do not prove a link-training failure, a cable fault or a 4K bandwidth limit.
- Historical W results used the original monitor. A W-versus-T1 comparison across different monitors/cables cannot isolate an image regression. Earlier D3/E failures remain separate cases with unknown causes.

## Smallest useful next investigation — proposal, not release

1. Confirm exact models, the lower/front port, direct USB-C connection and current boot. Obtain fresh attendance, healthy internal screen/system, open lid, MagSafe, battery above 50% and empty monitor USB-port confirmation before any device action.
2. Seek approval for one bounded unprivileged read-only snapshot with the new monitor left connected. Collect current kernel/loaded identity, exposed DRM connector status/modes/EDID, compositor output state and a bounded kernel log. Keep raw identifiers and EDID serials private. Review exact reads first; no forced detect, modeset, AUX/I2C/register probe, debugfs, sudo, fallback or partner `usb_mode` read. An unavailable field remains unknown.
3. Then propose one attended cable cross-test: use the original monitor's known-working cable with the new monitor on the same port and boot. David performs the swap only after separate approval. Record both cable identities and output behavior; take a separately approved matching snapshot. If ambiguity remains, consider the reverse combination, not an automatic four-case ladder.
4. Find the first difference: connection/EDID discovery, link establishment and valid modes, or compositor output selection. Consult the exact LG manual after model identification. A lower-bandwidth advertised mode is a later separately approved, temporary test with explicit rollback; do not force EDID, change firmware or patch timing on this evidence.

The first snapshot and cable comparison need no new image or reboot. Startup reliability needs its own later test; hotplug success cannot establish it. W recovery remains available by separate approval if needed, not the immediate investigation step. All prior live-action holds remain until a specific release.

Linux documents EDID, valid mode properties and optional `link-status` reporting separately. Use the kernel's mode list rather than raw EDID alone for usable modes. Missing `link-status` is missing evidence, and default GOOD does not prove pixels reach the monitor. See [standard DRM connector properties](https://docs.kernel.org/gpu/drm-kms.html#standard-connector-properties).

## Work performed and limits

Reviewed David's reports, the saved T1 journal and earlier display evidence. Updated the two living plans without modifying historical evidence. No new live capture, monitor action, runtime/configuration edit, build, staging, sudo or reboot ran. No root cause or fix is established. The [main plan](../plans/dev-147-m2-displayport.md#minimum-remaining-path-living) owns next-step authority.
