# Second front-port reconnect — 2026-09-05

David unplugged the display, waited about five seconds and reinserted it in the same front USB-C port. He reports an image after another 10–12 seconds. Current DRM state is connected/enabled. This is the second successful reconnect observation on the candidate kernel.

The [bounded log snapshot](dev-147-fairydust-front-reconnect2-2026-09-05.json) records:

| Event | Boot-relative seconds |
|---|---:|
| DPTX disconnect | 1647.674343 |
| DPTX connect | 1662.720527 |
| HPD connected with 16 modes | 1664.980690 |
| 3840×2160 nominal 60 Hz modeset completed | 1665.250589 |

The disconnect-to-connect gap is 15.046 seconds. Once DPTX connection starts, modesetting completes in 2.530 seconds, close to the first reconnect's 2.543 seconds. USB host registration also resumes near the later connect event, and LG monitor controls enumerate afterward. This is enumeration evidence, not a USB transfer test.

Given the approximate five-second unplugged interval, the user's observation is consistent with much of the delay preceding the logged DPTX connection. Physical reinsertion and visible-image timestamps were not instrumented. These logs cannot assign the delay to the cable, monitor, PD negotiation or kernel driver.

Firmware services now use channel IDs 5 and 7, after 1 and 3 on the first connection. These IDs alone do not prove a host service-slot leak or validate the AFK reuse patch. Two successful reconnects do not establish endurance beyond the previous failure window. Startup detection, latency, the other port/orientation, audio, charging and suspend remain open.
