# DEV-147 contribution drafts — 2026-08-28

Status: UNSENT. These are review drafts, not submitted issues, comments, or pull requests. The [living plan](../plans/dev-147-m2-displayport.md#fork-integration-and-upstream-contribution) owns approval and next actions. Hardware statements below come only from saved tested evidence; no new trial was performed for this draft.

## Contribution checks

- A read-only check of [haripako/dp-altmode](https://github.com/haripako/dp-altmode) found no explicit `LICENSE`, `CONTRIBUTING`, or AI-contribution policy. Confirm terms, the preferred channel, and acceptance of material AI assistance before submitting. Absence of a policy is not permission.
- [Omarchy Mac PR #289](https://github.com/omarchy-mac/omarchy-mac/pull/289), by haripako, was OPEN on 2026-08-28. It already proposes the DP-altmode explanation/diagnostic work. Do not open a duplicate; ask where a distinct M2 report would fit.
- [Asahi's Generative AI Policy](https://asahilinux.org/docs/project/policies/slop/) prohibits materially AI-assisted contributions, including engineering decisions and documentation. This work and these drafts are not compliant Asahi submissions. Human review or routing them through another repository does not remove that provenance. The inquiry below is for haripako, not an attempt to bypass Asahi's policy.
- Sending either draft needs David's separate approval and confirmed recipient terms. C2 offline approval does not authorize external communication.

## Draft A — limited M2 replication report

Suggested subject: One J413 M2 front-port DisplayPort result, with startup USB still open.

This is an adaptation of the approach documented in [haripako's M1 project](https://github.com/haripako/dp-altmode), not a claim that its M1 installer or board constants transfer unchanged. We tested one MacBook Air M2 J413/T8112 on kernel `7.1.6-1-1-ARCH`, with one monitor/cable on the front/lower left USB-C port. The rear port was not enabled or validated by this prototype.

Credit belongs to haripako for the reference investigation and to the Asahi contributors, including Janne Grunau and Sven Peter, for the upstream HPD work. Our [source history](../evidence/dev-147-prototype-history-2026-08-27.md#historical-stock-baseline-and-initial-research) records the exact M2 DT and CD321x HPD source commits. Existing author notices and per-file licenses remain intact. The reference installer/DTB was not run on the M2; the full reference kernel and `appledrm` workaround were not adopted.

| Saved case | Result and limit |
|---|---|
| [Initial contained prototype](../evidence/dev-147-prototype-history-2026-08-27.md) | Patched M2 DT routing and HPD core produced external video in the live test. This was not permanent integration. |
| [One-time working-image startup](../evidence/dev-147-one-boot-startup-2026-08-27.md) | Both physical screens worked: internal 2560×1664 at 60 Hz; external 3440×1440 at 99.982 Hz. Monitor USB hub/controls were absent. |
| [One attended reconnect](../evidence/dev-147-usb-reconnect-2026-08-27.md) | Internal screen stayed usable; external image returned in about five seconds by user report. The monitor hub and controls enumerated. This was one functional case, not repeated-hotplug reliability. |
| [D3 diagnostic startup](../evidence/dev-147-usbdiag-startup-failure-2026-08-28.md) | External video failed while the internal screen remained usable. A defective diagnostic target guard suppressed the trace; it does not explain the video failure. |
| [Separate working-image recovery](../evidence/dev-147-dp-recovery-2026-08-28.md) | Both native displays and responsiveness returned with packaged USB drivers and the working patched DP core. Only root hubs enumerated; startup USB remains HOLD. |
| [C1 diagnostic correction](../evidence/dev-147-usbdiag-c1-correction-2026-08-28.md) | Exact OF-node guard correction and strict v2 identity passed userspace tests after genuine RED. This is instrumentation source only, not a tested USB/video fix or a v2 boot result. |
| [C2 offline preparation](../evidence/dev-147-c2-offline-preparation-2026-08-28.md) | Fresh control/v2 modules and the E-only image passed offline checks and independent QA. E remains unbooted. This adds no USB/video fix or new hardware result. |

Firmware diagnostics remain unresolved, including an unplug-time FIFO error. A separate diagnostic status read caused a recorded WARN; it was not repeated. These are not clean-log claims. No repeated hotplug, cold-start, suspend, rear-port, downstream-peripheral, or full-rollback acceptance is established. Full Gate 4b remains HOLD, and D3 video causality remains unknown. No safe general installation or kernel-update integration is claimed.

Material AI assistance was used in investigation, source/tests, engineering decisions, documentation, and this draft. Physical actions and visible results were reported by David and checked against the saved evidence. Raw journals, device identifiers, and private machine paths are not part of this draft.

## Draft B — maintainer inquiry to haripako

Hi haripako,

Your DP-altmode investigation helped us adapt the route and HPD approach to one J413 M2 MacBook Air. We have a limited display-success report, an unresolved attached-startup USB issue, and a separate failed diagnostic boot followed by recovery. We are not presenting this as a general fix.

The work and the proposed report used material AI assistance, including code, investigation, engineering decisions, and writing. Before sharing a report or patch, could you confirm the repository's license/contribution terms and whether you accept work with that provenance?

I saw your open [Omarchy Mac PR #289](https://github.com/omarchy-mac/omarchy-mac/pull/289). If a narrow M2 report is welcome, which channel should it use so it does not duplicate your work? We would preserve the upstream author credit and keep our failures and untested cases explicit.

No message has been sent. Do not forward this draft to Asahi or treat it as permission to submit code.
