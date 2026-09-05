# Front-port stability: initial probes — 2026-09-05

The [front-port stability plan](../plans/2026-09-05-dev147-front-port-stability.md) now owns acceptance and release work. The running candidate remains unchanged. This milestone prepares measurement and identifies the next diagnostic; it does not establish a stable release.

## Independent source probe

The frozen private receipt `/home/david/Work/dev147-fairydust-acceptance-20260905/source-review/source-review.json` has SHA-256 `2e5cd0f0fe2bf72eeac98305bd765562cd00b2946f88289f027691c12adb5852`. It pins the inspected source, line references, filtered journal and detailed source note. Kernel HEAD is `83604c8b18e4673ed91e1172aef9aebeb0af20ce`, with a clean source tree.

`drivers/gpu/drm/apple/afk.h` defines 16 service records per endpoint. Each successful endpoint 0x28 announcement consumes or reuses one record. Two services appear per observed display generation. The ninth pair therefore crosses stock capacity; the existing extracted-source harness tests ten quiescent generations. A twenty-generation hardware target gives additional bounded coverage, not proof of indefinite stability.

The 11:17:24Z same-boot snapshot contains 12 accepted endpoint 0x28 announcements and one external DCP boot. That is six observed announcement pairs. Visual confirmation for the newest three reconnects is pending. Numeric firmware channel IDs and repeated DPTX connect calls are not host slot counts or physical reconnect counts.

There is no unprivileged direct counter for host retirement/reuse in this source. More than 16 accepted announcements during one unchanged endpoint lifetime can establish progress beyond the original capacity. It cannot prove every internal reference or retirement invariant. The source harness and independent review cover those distinct claims.

## Startup diagnosis

CD321x already reads attached state at probe and queues a delayed update (`drivers/usb/typec/tipd/core.c:1731`). Its work sends connection status through `drm_connector_oob_hotplug_event`. That function returns without retaining the notification if the connector is not found (`drivers/gpu/drm/drm_connector.c:3527`). The global lookup list receives the connector at DRM registration, after Apple DCP startup/readiness. The later DCP HPD replay path is guarded by an HDMI GPIO absent from J413.

This establishes a possible lost-notification window. It does not prove that this boot sent HPD in that window. The observed early xHCI start, later external DCP boot, and absence of Apple OOB callback logs until unplug are consistent with it. Next, correlate initial CD321x HPD state and send time against connector registration. Do not add a delay or speculative replay patch before that probe.

The source review also notes a cached mux-mode path that ignores the mux-set result. No observed failure establishes this as the cause; keep it separate from the primary hypothesis.

## Upstream boundary

`git ls-remote` still reports fairydust `b8810ad6442699f610984f3eceea2e3234a50b77` and `bits/200-dcp` `52f0b76aaae7b9a1cc2100f4a9b33257b450d5c0`. These branches have no newer tip to substitute for the audited baseline. This is not a search of every submission. Recheck novelty and maintainer conventions when preparing the isolated AFK contribution.

## Collector correction and scope

The [acceptance collector](../../dev/apple-dp-altmode/fairydust/acceptance/README.md) runs without sudo and writes unique private snapshots. It records selected state and categorized diagnostics; it never decides visual success or endurance acceptance.

Independent QA found that the initial summary combined announcements from separate controllers. An actual-entry-point fixture with ten announcements on each controller returned twenty. The corrected summary explicitly selects external DCP `271c00000.dcp` and endpoint `0x28`; that fixture now returns ten. Endpoint text is parsed as hexadecimal. The failed counterexample remains in `collector-independent-qa/mixed-controller-counterexample.json` under the private acceptance root.

The corrected author gate exits 0 at `checks/collector.ivHF8J3n`. It runs eight entry-point controls, Ruff, formatting, strict mypy, shell syntax and a live capture integrity check. The live snapshot is `SNAPSHOT_CAPTURED_WITH_ERRORS`: twelve external announcements/six count-pairs, nine classified firmware error records, zero classified host error records and no collection issues. This is honest evidence collection, not a clean-hardware PASS. Diagnostics cover selected drivers for fifteen minutes; service/boot records cover the current boot subject to explicit limits.

Independent QA reruns the full gate at `checks/collector.s1QPrrz2`, exit 0, with no remaining blocking finding. Its frozen receipt `collector-independent-qa/final-qa.json` has SHA-256 `da97ee756b8f3104b4c783cd7fb4b0a3a6735144d438ab86daac5291e8ae207f`. The [bounded milestone receipt](dev-147-front-stability-start-2026-09-05.json) binds source and private proof hashes. Only plan Slice 1 is complete; human outcomes, endurance, diagnosis, release and upstream contribution remain open.

Namespace controls substitute DRM/Type-C state and command outputs while retaining live protected pins and boot ID. Read-only output modes and hash manifests do not prevent owner tampering. The known unsafe Type-C `usb_mode` is represented by an unread FIFO in a control and is not queried. No selected boot, kernel or system configuration changed.
