# DEV-147 attachment after requested monitor reset — 2026-09-05

David ran the attach recorder after the requested monitor power-cycle procedure. The command exited 0. Explicit confirmation of the physical power steps, visible outcome and rear-port accessory is still pending.

Private result: `/home/david/Work/dev147-fairydust-acceptance-20260905/trace-capture.987OT1x4`. Report SHA256: `e7076f037194eaf10d39c4131868a0af936b36c7af7c5605f83e8e237d7d221f`. The report identifies attach mode and unchanged boot `f80d5566-d14a-4374-9824-15887a63c576`. Its 8404.89–8449.89 second window retained 28/28 records, with all 24 loss counters zero. Cleanup removed its instance.

Front-controller thread `irq/117-0-003f` reports attachment at 8419.796235. Four data-status records at 8419.798729, 8419.842498, 8419.916937 and 8420.838724 retain USB_DATA_ROLE. USB2/USB3 flags appear transiently and then disappear. No record reports DP_CONNECTION or HPD_LEVEL. There are no selected DCP/IOMFB trace records. The bounded journal reports DPTX disconnect at 8420.649854 and 8421.346355, with no corresponding connect.

The read-only snapshot `after-monitor-reset-attach.h64s12rv` reports DP disconnected/disabled and internal eDP connected/enabled. It exits 0 with no classified journal errors or collection issues. That status means successful evidence capture, not working hardware.

The observed state remains the negotiation failure described in the [preceding capture](dev-147-targeted-reconnect-failure-2026-09-05.md). This attempt provides no evidence that monitor-side power cycling restored negotiation. It cannot identify a host-only cause or exclude cable, monitor or retained controller state. Do not repeat an identical reconnect batch or the previously rejected host-role request. Confirm the physical outcome and attached equipment before selecting a different cable/monitor comparison or a host restart for recovery.

Attach-mode independent software QA receipt: `/home/david/Work/dev147-fairydust-acceptance-20260905/checks/trace-attach-independent.0scd4fmi/receipt.json`, SHA256 `edaff3f4c6ac1c2c5fb719d4a5e37a328e8bca7fca90ab83bfdc3a70fd61dfae`. Six test methods, syntax, Ruff, formatting, strict typing and diff checks passed before this manual run.

Independent review re-derived trace counts, loss counters, cleanup and snapshot integrity. It also found that rear `port0` changed from host/source with a partner in the prior failed snapshot to device/sink without a partner now. Overall attachment topology was not constant. The preferred next discriminator, if already available, is one known-working USB-C video cable on the same monitor/front port and current failed Linux boot. The rear connection must be identified first.
