# DEV-147 integrated candidate internal confirmation evidence — 2026-09-02

**Host / scope:** `omarchy-air`, M2 MacBook Air J413, integrated DisplayPort candidate
**Approval:** proceed-and-report tier; David supplied the requested physical confirmation
**Repo state:** `4af73cc5d3f3d1b4625fd359f74740369302f868` before this evidence commit

## What happened

After the successful LG27-to-LG35 switch, David confirmed that the built-in
screen worked normally and that the system remained responsive. No further
cable action, suspend, reboot, mode change, or driver action occurred before
the read-only confirmation snapshot.

## Result

The physical internal-panel confirmation closes the remaining Slice 3 input.
The same boot `fa500274-a4fd-49e3-a84a-82ec4948b8e3` still returned:

- `eDP-1` connected and enabled at 2560×1664/60 Hz with DPMS on;
- `DP-1` connected and enabled at 3440×1440/99.982 Hz with DPMS on;
- zero failed systemd units;
- zero fatal kernel patterns in the bounded scan;
- responsive command execution at 1,575 seconds of uptime.

Together with the prior candidate records, this proves internal-only startup,
LG27 attachment at native 4K60, one same-boot switch to LG35 at native
3440×1440/99.982 Hz, a normal physical internal panel, and responsive Linux.

## Rollback

This confirmation and snapshot were read-only. They changed no system state.
The installed candidate retains its existing EFI backup and recovery guide.
The documentation change is reversible through Git.

## Open

- Attached-display suspend is unsupported. Do not repeat the failed test.
- Hot-switch EDID and compositor monitor identity can stay stale.
- Monitor USB-data reliability remains separate in DEV-163.
- The retained `disablehooks=encrypt` token still qualifies this boot. A later
  boot-configuration cleanup owns an unqualified production-argument run.
