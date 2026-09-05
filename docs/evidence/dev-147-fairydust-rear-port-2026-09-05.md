# Near-MagSafe display attempt and fixed routing — 2026-09-05

David moved the monitor from the front USB-C port to the port nearest MagSafe, after about five seconds unplugged. It showed no image after 20 seconds. DRM reports external DP disconnected/disabled; internal eDP stays connected/enabled.

Same-boot logs show the previous DPTX disconnect at 1804.514381 seconds. A USB host controller starts at 1811.150160 seconds with MMIO base `0x382280000`, unlike the front-port controller's `0x502280000`. No later DPTX connect or external modeset appears in the sampled log. Type-C `port0`, under CD321x address `0x38`, has a partner, host data role, sink power role and USB Power Delivery mode. This establishes partner/PD detection, not a successful USB data transfer or measured charging performance. The known-problematic `usb_mode` attribute was not read.

The frozen source explains a routing limitation: `arch/arm64/boot/dts/apple/t8112-jxxx.dtsi` attaches `displayport = <&dcpext>` only to `typec1` at address `0x3f`. Its external DCP selects `apple,dptx-phy = <1>`, `atcphy1` and `atcphy1_xbar`. The live device tree also reports DPTX PHY index 1. The other connector has no equivalent display binding in this source. These inputs, the front-port successes and the current Type-C partner mapping support the conclusion that this build supplies a fixed front-port display route. The unsuccessful rear-port test is consistent with that limitation, rather than proof of broken hardware.

The agent should have checked this fixed route before requesting the second-port test. Both-port display support remains implementation work. Do not duplicate the display pointer or change the PHY number on the running stack: that alone does not establish safe dynamic routing, arbitration or correct hot-plug handling. Review the coherent upstream routing work before deciding what local changes remain necessary.

Return to the front port for the known-working display baseline. Track three separate gaps: detection when attached at boot, delayed hot-plug detection, and display routing for the port near MagSafe. Keep reconnect endurance, USB/audio/charging and suspend acceptance open.
