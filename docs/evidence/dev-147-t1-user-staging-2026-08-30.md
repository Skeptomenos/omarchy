# DEV-147 T1 user-run staging — 2026-08-30

Status: user-run staging PASS, with independent receipt QA PASS. David completed the one authorized invocation of the pinned private helper. The staging release is consumed. T1 remains UNBOOTED; no capture, cable change, recovery action, or hardware result follows.

## Accepted receipt

Saved stdout is exactly 6,098 bytes and 48 lines: the accepted 5,870-byte, 45-line protected/proof prefix followed by the exact three completion lines. Full output reconstruction matches its hash. Stderr is empty. The exit file contains exactly `0\n`, corroborating David's pasted `Recorded staging exit 0` report. The three records retained stable mode 0600, one link, and UID/GID 1001; their parent directory is mode 0700.

| Record | SHA-256 |
|---|---|
| stdout | `a7b1d362f9705b3d8bd1ac035cae507040d1f82bc01e9338525330cc305d0eba` |
| stderr | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| numeric exit | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

The helper SHA-256 remains `6b20d119791f4322e101a92b9e5b850ba3098d35dbf966f2d7918cb3918694f9`; the held handoff remains `1f700c2f623040b7dbc34c1c24679de49cbeb0294017698c61d64e5ddc624db3`. Main-agent record review and independent QA passed. The accepted destination is `/boot/initramfs-linux-asahi-dpalt-tipddiag1.img`, with expected size 19,209,545 bytes and SHA-256 `c72c36736cebba0d6d5b67f47b02330c35d3ef81fed9bf5b3315095b0dd765fe`.

Destination-byte checks, root-private transaction checks, and preservation of the default/W/EFI files are checks performed by David's pinned privileged helper. They are not fresh independent agent reads of `/boot`. Normal default selection remains unchanged according to that helper. A provisional result file alone is not the acceptance evidence.

The [sealed package](dev-147-t1-manual-package-2026-08-30.md), accepted image, and 54/13-method offline results remain unchanged. No helper replay, agent sudo/preflight/live sampling, rebuild, or test rerun occurred. Raw records, host paths, transaction names, and machine identifiers remain private.

## Next boundary

STOP for a separately approved attended T1 test. The latest user-reported setup has no USB-C connection. The proposal needs fresh readiness and setup confirmation, front/lower monitor reconnection, exact T1 GRUB selection, and the fixed bounded capture; none is authorized by staging PASS. Conditional W recovery requires separate approval in that later release. Keep all boot, live-capture, cable/device, recovery/suspend, runtime-expansion, and upstream holds. No monitor, USB, power, or reliability PASS is claimed.
