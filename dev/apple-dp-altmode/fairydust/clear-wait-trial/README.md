# Clear-swap wait diagnostic

This trial tests whether a 100 ms wait lets the observed late clear-swap reply finish before display shutdown continues. The [front-port stability plan](../../../../docs/plans/2026-09-05-dev147-front-port-stability.md) owns status and hardware acceptance. The [trace evidence](../../../../docs/evidence/dev-147-fixed-x8-reconnect-timeout-2026-09-05.md) explains the 51.749 ms observation.

The only driver change is 50 to 100 ms in `iomfb_poweroff`. It retains the timeout warning and PR582 recovery behavior. This is a diagnostic budget, not a measured worst-case bound.

## Inputs and flow

Frozen fairydust1 source → one-line patch → separate Image/modules/DTB → offline gates → isolated initramfs → later attended boot.

- Parent: `83604c8b18e4673ed91e1172aef9aebeb0af20ce`.
- Trial: `d2f36591abdb0db296ac24e5a2b9dade5ae40ef1`.
- Root: `/home/david/Work/dev147-clear-wait-trial`.
- Release: `7.1.12-dev147-clearwait100`.
- Config SHA-256: `f69e63e55cbc6b257a951c82b3e581ffc60d4614a5965561cbc322960767bdff`.

Only the release name differs from the baseline config. The private `build-command.sh` records the pinned toolchain and build environment. No additional environment keys are required by the validation scripts.

## Checks and build

Run the completion gate from this directory:

```bash
bash validate.sh
```

The gate extracts six completion functions from the pinned Linux source. A deterministic C harness tests a 52-tick reply against baseline and candidate budgets, absent and late replies, and deadline boundaries. It does not execute DCP callbacks, poweroff, RTKit or KMS. Passing it cannot prove callback lifetime or hardware recovery.

Compile in the separate output tree:

```bash
/home/david/Work/dev147-clear-wait-trial/build-command.sh Image modules apple/t8112-j413.dtb
```

Compilation uses resumable 280-second checkpoints. A final zero exit is required. After private module installation and depmod, assemble and validate:

```bash
bash assemble.sh
bash validate-build.sh /home/david/Work/dev147-clear-wait-trial
```

The full gate checks source/config identity, Image, all staged modules, BTF, device-tree relationships and retained AFK controls. The source bundle contains three local commits and requires upstream base `b8810ad6442699f610984f3eceea2e3234a50b77`.

Then build an initramfs in an unprivileged namespace:

```bash
bash initramfs/build.sh /home/david/Work/dev147-clear-wait-trial /home/david/Work/dev147-clear-wait-trial/initramfs/run-001
bash initramfs/validate.sh /home/david/Work/dev147-clear-wait-trial/initramfs/run-001/initramfs-7.1.12-dev147-clearwait100.img
```

Use a fresh output directory for each attempt. These procedures do not install or select a kernel. Hardware acceptance must check shutdown-tail calls, timeout behavior, visible image recovery and existing regressions after an attended boot.

The [preparation evidence](../../../../docs/evidence/dev-147-clear-wait-trial-preparation-2026-09-05.md) records completed source and recipe checks. The living plan tracks later build and hardware results.

Use the [stage-only guide](stage/README.md) after artifact validation and delivery rehearsal. It explains temporary boot selection and the retained default.

## Attended acceptance

The trial's capture tools retain an exact release guard and separate output root. Check their software controls before boot:

```bash
bash acceptance/validate.sh
```

After the attended trial boot, collect read-only state with `python3 acceptance/snapshot.py trial-boot`. Use `bash acceptance/trace-capture.sh` only for an agreed front-port reconnect. The original baseline tools remain unchanged.

A successful clear-wait trial needs a loss-free trace of A407/A408 replies followed by the A467 → A457 → A472 shutdown chain, no clear-swap or power-state timeout, later DP/HPD recovery and user confirmation of the image. Transport ACKs do not expose callback status or the completion cookie. USB/ATC warnings require separate journal review. The snapshot's quiet-journal and driver-filter limitations remain disclosed in the living plan.
