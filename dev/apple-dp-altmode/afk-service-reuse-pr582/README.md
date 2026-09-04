# AFK reuse with PR582 timeout semantics

This directory composes the accepted AFK service-reuse prototype with the
poweroff timeout behavior from Asahi Linux pull request 582.

Apply these patches in order to the exact accepted Asahi source commit
`e2e1930a9595bffafad92cec2b5504525efb9cd4`:

1. `../afk-service-reuse/afk-service-reuse.patch`
2. `pr582-timeout.patch`

The second patch keeps the 50 ms wait and the immediate timeout return. It
replaces only the timeout-path `dcp->crashed = true` store with a warning. The
RTKit crash callback remains the only writer of `dcp->crashed`. The atomic
guard remains unchanged.

Francisco Vargas authored and tested the PR582 timeout semantics. The local
patch omits the upstream explanatory C block comment to comply with this
repository's source-comment rule. See `../pr582/pr582-upstream.patch` for the
original patch, attribution, and provenance record.

Run the retained RED and the full source contract:

```bash
python3 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test_combined_candidate.py \
  --source-root /home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux \
  --red-only

python3 -I -S -B dev/apple-dp-altmode/afk-service-reuse-pr582/test_combined_candidate.py \
  --source-root /home/david/o/.dev147-stage/dev147-integration-source.SGVnPytGQN/linux
```

The first command must exit 1 because the AFK-only source still writes the
permanent crash flag on the poweroff timeout. The second command applies both
patches in a temporary directory. It checks exact source identity, patch
scope, timeout control flow, the genuine crash writer, the atomic guard, and
negative mutations. It also runs the existing AFK lifecycle suite.

This candidate is not a default image or an upstream-ready patch series. It
does not authorize staging, loading, rebooting, cable changes, or boot changes.
