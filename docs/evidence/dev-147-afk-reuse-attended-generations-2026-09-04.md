# DEV-147 AFK reuse attended generations

**Date:** 2026-09-04
**Host:** `omarchy-air`
**Kernel:** `7.1.6-1-1-ARCH`
**Candidate:** `/boot/initramfs-linux-asahi-m2-displayport-afk-reuse.img`
**Boot ID:** `061c4b0f-2ca9-484a-b6f0-005d9a432d3b`

## Candidate identity and setup

David selected the non-default AFK reuse candidate for one attended boot. The command line includes the existing `disablehooks=encrypt` qualification. The loaded AppleDRM GNU build ID is `1ca52ad1cea00559d5fdfd32177e4d1e694994e1`, which matches the candidate module. The internal display stayed usable, and Linux stayed responsive.

The test used the LG 27UN83A-W, its known-good cable, and the lower/front left USB-C port. The monitor USB ports were empty. MagSafe supplied independent power.

## Reconnect results

| Generation | Physical result | Endpoint `0x28` service channels |
|---|---|---|
| 1 | Cable attach did not wake the monitor. One joystick action woke it, and the image appeared about five seconds later. | `1`, `3` |
| 2 | Disconnect, wait five seconds, and reconnect restored the image about five seconds later. | `5`, `7` |
| 3 | The same controlled reconnect restored the image about five seconds later. | `9`, `11` |
| 4 | The same reconnect did not restore the image. A later joystick action did not recover it. | No new service |

The internal display and Linux remained healthy after generation 4.

## Generation 4 failure boundary

After the failed reconnect, the Type-C partner remained present and monitor power delivery remained online. DRM reported `DP-1` as disconnected and disabled. The `dwc3-apple` platform device remained driver-bound and runtime-active, but its xHCI child was absent.

The failed controller state reported `data_role=host [device]`. Linux brackets the active Type-C data role, so this means that the device role was active. No UDC or xHCI device was present. A retained private capture from older boot `756f3290-0e6d-45c9-af66-63ddb37d06ed` reported `data_role=[host] device` for the same `0-003f` controller while its xHCI root hubs existed and LG35 ran at 3440x1440. The older capture used a different monitor, so this is not a matched LG27 comparison. The role difference is correlated with the failed transition, but it does not prove cause.

The disconnect removed xHCI at 984.680 to 984.683 seconds. DPTX removed HPD at 991.745 seconds. Firmware reported `inCmd:0`, `inResp:0`, `outRepErr:0`, and `outCmdErr:0` for the old channel 9 and 11 interfaces. These counters do not prove the full AFK reuse retirement contract. DCP disconnected at 991.789 seconds. Reconnect produced only status `0x2` and disconnect handling at 1000.553 and 1001.340 seconds. The later joystick action again produced only status `0x2` at 2384.216, 2397.712, and 2398.505 seconds.

No endpoint `0x28` service appeared after channels 9 and 11. The journal contained no service-capacity or announcement error. The monitor USB hub also flapped repeatedly at 978 to 980 seconds before xHCI teardown.

## Result

The candidate boot and its first three display generations worked. Generation 4 failed during the Type-C, USB, or DPTX transition before AFK service allocation. It did not reach the service-reuse boundary and does not validate or reject the AFK fix.

The ten-generation AFK test remains open. Stop the reconnect loop until the pre-AFK transition failure is isolated or a controlled path around it is reviewed. The USB activity is adjacent to DEV-163, but this evidence does not establish a shared cause.
