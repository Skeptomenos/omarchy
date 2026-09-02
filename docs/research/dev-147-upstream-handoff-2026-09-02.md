# DEV-147 upstream handoff — 2026-09-02

**Status:** Prepared, not submitted
**Issue:** DEV-147
**Local draft PR:** [Skeptomenos/omarchy-mac#1](https://github.com/Skeptomenos/omarchy-mac/pull/1)

## Current upstream state

[Omarchy Mac PR #289](https://github.com/omarchy-mac/omarchy-mac/pull/289)
is open against `quattro`. It adds DisplayPort diagnostics and documentation.
It deliberately does not enable DisplayPort. Its current review state is
changes requested. The latest review disputes the detector's device-tree model
on real Apple Silicon hardware. DEV-147 must not depend on that detector or
duplicate its unresolved diagnostic work.

The Omarchy Mac repository has no root or `.github` contribution guide at this
check. Its [MIT license](https://github.com/omarchy-mac/omarchy-mac/blob/quattro/LICENSE)
permits modification and redistribution with the license notice retained.

The [Asahi Linux contribution page](https://asahilinux.org/contribute/) binds
contributors to its [Generative AI Policy](https://asahilinux.org/slop/).
That policy expressly forbids LLM use in any contribution when code,
documentation, or engineering decisions are materially created with it. This
session is materially AI-assisted. Do not submit its code, documentation,
findings, comments, issue reports, or patch descriptions to any Asahi Linux
repository or project space.

## Recommended Omarchy Mac path

First send one short, human-reviewed hardware-evidence comment to PR #289. Ask
whether the maintainers want a separate experimental enablement PR. This avoids
placing a large opt-in workflow into review before the maintainers accept its
scope. If they request code, open a separate draft PR from
`Skeptomenos:codex/dev-147-m2-displayport-opt-in` to `omarchy-mac:quattro`.
Keep AI assistance, hardware provenance, safety limits, and the three unrelated
aggregate-test failures explicit.

Do not merge the local draft into `quattro-arm` before the active format-1
installation is rolled back with the exact legacy script and replaced by a
format-2 preparation. The code review found this migration boundary after the
first live validation.

## Prepared PR #289 comment

The following text is a draft. It has not been posted:

> We tested the M2 MacBook Air J413/T8112 path on `linux-asahi
> 7.1.6-1-1-ARCH`. A fairydust-derived J413 device-tree change plus the TIPD
> hotplug-forwarding change produced native USB-C DisplayPort video on the
> lower/front left port. The integrated candidate passed an internal-only
> startup, LG 27UN83A-W attachment at 3840×2160/59.997 Hz in about five to six
> seconds, and one same-boot switch to an LG 35 ultrawide at
> 3440×1440/99.982 Hz in about five seconds. The built-in panel remained normal
> and Linux remained responsive.
>
> The result is still experimental. Attached-display suspend failed and is
> unsupported. EDID and Hyprland monitor identity can stay stale after a hot
> switch. Monitor USB data can disappear independently of video. The tested
> boot also retained an unrelated `disablehooks=encrypt` argument, so we record
> the result as qualified and exclude that argument from all instructions.
>
> We prepared a separate reversible opt-in workflow with exact model, kernel,
> image, module, m1n1, and U-Boot pins; separate preparation and activation;
> a package-update guard; a root-owned checksummed rollback entrypoint; and an
> EFI Recovery Terminal path. The reviewed draft is
> https://github.com/Skeptomenos/omarchy-mac/pull/1. Development and this draft
> were materially AI-assisted. David supplied the physical hardware tests.
>
> Would you prefer a small evidence/documentation follow-up to this diagnostics
> PR, or a separate experimental enablement PR after you review the scope?

## Submission gate

David must review and approve the exact text before it is posted. Posting the
comment or opening an upstream Omarchy Mac PR is external communication. A
maintainer request for code does not authorize merging or deploying the local
draft. Asahi submission remains prohibited by project policy.
