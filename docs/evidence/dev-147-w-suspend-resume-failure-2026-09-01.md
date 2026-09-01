# W suspend/resume failure — 2026-09-01

Result: DEV-147 Case E FAIL with safe user recovery. Exact W did not restore a usable session with LG35 attached. The external DCP failed link preparation and native modeset during resume. David recovered the internal login by disconnecting LG35 and waking the computer again. Do not repeat this case.

## Pre-suspend state

Boot ID `261ba5db-68fc-4044-8cd8-09687a5fcba3` was the accepted W boot used for Case D. David had selected:

```text
initrd /boot/initramfs-linux-asahi-dpalt.img
```

Immediately before suspend, eDP-1 was active at 2560×1664/60 Hz and LG35 DP-1 was active at 3440×1440/99.982 Hz. Both had DPMS on and neither was mirrored. MagSafe and monitor power delivery were online. The battery was Full/100%. No systemd unit had failed and no job was active.

## User-observed result

David suspended once with the lid open, MagSafe connected, and LG35 still attached. He waited approximately 15 seconds and woke the computer. After a delay, only the internal image appeared and it was not responsive to password input. He disconnected the external monitor, woke the computer again, and could then enter the password. The external monitor remained disconnected for capture.

The later recovery required more than one short power-key press. This does not change the test classification. The failed attached-resume state was preserved until the recovery cable removal.

## Captured sequence

| Local time | Event |
|---|---|
| 22:27:22.085 | systemd-logind accepts the one suspend request |
| 22:27:23.289 | Kernel enters `s2idle` |
| 22:27:43.944 | System returns from suspend after about 20.7 seconds of wall time |
| 22:27:43.967 | External DCP receives `dcp_dptx_connect(port=0)` |
| 22:27:43.968 | `IOAVVideoInterface prepareLink()` fails with `0xe00002ed` |
| 22:27:43.969 | LG35 3440×1440 modeset fails; the external pipe remains disabled and returns `80000104` |
| 22:27:43.970 onward | External swaps are swallowed because controller power and timings are off |
| 22:28:36.302 | External DCP receives `dcp_dptx_disconnect(port=0)` after David removes the cable |
| 22:28:50.148 | Omarchy lock records a successful unlock |

The same resume interval records `xHC error in resume, USBSTS 0x401, Reinit` and both USB root hubs losing power or being reset. That concurrent USB result does not establish the cause of the display failure and remains outside DEV-147 video acceptance.

The internal DCP also power-cycled during resume. It requested 2560×1664 and returned `8000000b`, then published its interface. This evidence does not isolate whether the unusable internal lock screen came from DCP, compositor, focus, or lock-state handling. The user-visible recovery coincides with external cable removal, internal-DCP reinitialization, later wake input, and unlock.

A bounded strict scan finds no kernel BUG/panic/Oops, DART/IOMMU fault, RTKit/coprocessor crash, or AFK exhaustion. systemd reports the suspend transaction itself as successful. That service result does not override the failed display/session acceptance result.

## Post-recovery state and consequence

The machine remains on the same boot. eDP-1 is connected, enabled, and responsive at 2560×1664/60 Hz. DP-1 and monitor power delivery are offline because the cable is physically disconnected. MagSafe remains online, battery is Full/100%, the user session is active, and there are no failed units or active jobs.

Cases A through D remain valid. This failure blocks default-on support and establishes suspend with an external display attached as an unsupported first-release path. It does not block reversible opt-in packaging because the plan defined Case E as a classification gate. No retry, reconnect, reboot, driver action, boot-file change, mode command, or recovery rehearsal follows from this result.

The exact W filename, visible pixels, responsiveness, input behavior, cable removal, and password recovery are user provenance. Boot identity, wall-clock suspend interval, DCP/USB messages, current DRM/compositor state, power, and systemd state are same-boot software observations.

Independent fresh-context verification PASS. It rechecked wall-clock timing, external-DCP failure messages, recovery ordering, current internal-only state, corrected fatal-pattern scan, plan history, local links, and diff hygiene. No claim is disputed. Physical pixels, password interaction, cable action, and exact W selection remain explicit user provenance.
