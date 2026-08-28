# DEV-147 — E selection confirmation and W recovery preparation

Date: 2026-08-28. This is an addendum to the unchanged [post-C4 display-loss record](dev-147-post-c4-display-loss-2026-08-28.md), not a new test or rewritten capture.

David answered the exact E-filename question with “yes, dpalt-usbearly1.img”. That confirms selection of the requested `initramfs-linux-asahi-dpalt-usbearly1.img`. Combined with the saved new-boot capture and display report, this records E external-display FAIL. Shared W/E module IDs alone would not prove selection. The cause remains unknown.

Fresh read-only checks at 19:56 UTC remain on the same boot as the sealed failure capture. Internal output is 2560×1664 / 60 Hz, tools respond, and the external output remains absent. Battery is 100%, Full; AC and both PD sources are online.

Kernel, seven package pins, loaded module IDs, taint 4100, and three image metadata records are unchanged. All 37 readable protected/proof hashes match. Root-private bytes retain the qualified C3 user-validator provenance; they were not independently reread.

No new full-journal or USB capture was made. The prior window's warnings, audit suppression, cursor caveat, and USB HOLD remain as recorded. Zero diagnostic markers are expected for uninstrumented E, not a trace failure.

The existing R-E review condition is now satisfied. Recovery release review passes. The [main plan](../plans/dev-147-m2-displayport.md#current-recovery-handoff--working-image-w-living) prepares the same one-use W procedure for final task release, with saved work, offline instructions, unchanged setup, responsive Linux, a usable screen, and safe restart required. W has not been performed.

The E handoff is consumed. No E retry, reconnect, B/G test, extra recovery attempt, helper execution, or privileged agent action follows. Keep images, backups, and evidence. Neither W nor normal stock boot restores the original DTB; W success is not guaranteed and Mac restore execution remains untested.

Full Gate 4b/USB acceptance, causality, reliability, full rollback, and upstream submission remain separate. Private boot identities, paths, and raw logs are excluded.
