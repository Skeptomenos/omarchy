# DEV-147 real archive controls — 2026-08-28

Status: 58 archive tests and the real no-change archive/index control PASS. No diagnostic image exists at this cutoff. D2 staging and D3 startup remain unauthorized. The working image and operational helpers are unchanged.

This follows the [offline helper QA](dev-147-offline-helper-qa-2026-08-28.md). Its 48 fixture passes remain valid at that cutoff, but did not prove compatibility with the real saved archive. The source checkpoint was pushed as `8bf097882b1f555f8c12bf1d317d275959f10068`; remote readback matched.

## Retained failure and format evidence

`run-qh6nm1d7` stopped during read-only real parsing with `zero archive link count`. It did not transform an archive, generate indexes, or create a diagnostic image. The failed helper and inputs remain retained. A separate bounded header inspection, `run-4w6029um`, found:

- All seven early records and all 1,162 main records have archive `c_nlink=0`.
- The main archive has 800 regular files, 194 symlinks, and 168 directories.
- Directory record names include a single trailing slash. The original bytes must remain intact.
- The existing ATC module, working DP core, and module indexes are regular records with archive link count zero. The saved image itself is a regular physical file with one filesystem link.

The pinned Linux consumer reads `c_nlink` without a positive-only check. Its `maybe_link()` takes the hardlink path only for counts of at least two. Thus zero and one both use the ordinary regular-file path. This is a source-backed compatibility rule, not a reason to relax filesystem hardlink checks. [Pinned Asahi consumer](https://github.com/AsahiLinux/linux/blob/e2e1930a9595bffafad92cec2b5504525efb9cd4/init/initramfs.c#L328).

The libarchive newc writer copies the entry link count and pathname into the record. It does not normalize either field at that point. This supports retaining the observed metadata; it does not establish why the earlier tar-to-newc pipeline produced zero counts. [Libarchive 3.8.9 writer](https://github.com/libarchive/libarchive/blob/v3.8.9/libarchive/archive_write_set_format_cpio_newc.c).

The correction is narrow: accept archive zero/one counts as non-hardlinked, and accept one trailing slash only on directory records. Canonical names are lookup keys; raw names and record bytes remain unchanged. Reject doubled/internal separators, traversal, duplicate canonical aliases, non-directory trailing slashes, and hardlink-group mutation. Physical input and output files must still have `st_nlink=1`.

Three independent regressions ran against the frozen first implementation in `run-0tb59_mr`. Two failed at the zero-count rejection; the unsafe-path case passed. This is an expected RED result. The original 16 fixture methods remain unchanged. All three retained runs reported unchanged inputs and no timeout.

## Correction and regression QA

The corrected [helper](../../dev/apple-dp-altmode/usbdiag/image/cpio_image.py) is pinned as `a32eddd159263d19ff87d7e9caee9d53d17ef5c350fbffe9e7eb142cb43ebf58`. Source review confirms that physical file checks are unchanged. One later fixture had wrongly required archive zero counts to fail; that expectation was corrected with the source evidence above. The original 16 methods remain unchanged. Seven compatibility tests were added.

`run-2sraoj50` passed 55 permanent tests plus the three unchanged [independent regressions](../../dev/apple-dp-altmode/usbdiag/image/test_review_archive.py): 58 total in 0.213 seconds. It used `python3.14 -I -S -B -m unittest discover -s /inputs/image -p '*test*.py'` inside the actual sandbox. Inputs were unchanged and no timeout occurred. This proves the tested format/filesystem behavior, not boot safety.

## No-change control

The first execution, `run-1lm74ilv`, passed exact no-op archive identity and full-image gzip reconstruction. It then stopped on an unexpected scratch output from depmod. The extra file was `modules.weakdep`, containing only its standard comment header. No binary-only lookup ran in that failed execution. All outputs remain retained.

The installed kmod is 34.2. Its source explicitly generates `modules.weakdep`. The installed mkinitcpio module builder removes non-binary indexes other than `modules.devname` and `modules.softdep` before packaging. The corrected control therefore permits this one scratch file, requires its exact header-only content, and never copies it to the binary-only lookup root or image. Any weak dependency entry or other output still stops the workload. [Pinned kmod output table](https://github.com/kmod-project/kmod/blob/v34.2/tools/depmod.c).

The corrected [control workload](../../dev/apple-dp-altmode/usbdiag/image/verify_control.py), SHA-256 `10b5afe6cff38df7b6ebe5619fd9a34935932a4b369f3a9ad2a51923c32932d8`, passed in fresh `run-bm5es0p7`:

- Independent GNU cpio and bsdtar listings agree with all seven early and 1,162 main records. Both no-op streams preserve every raw record, trailer, and zero tail.
- GNU gzip stdin defaults reconstruct the complete image byte-for-byte: SHA-256 `ae8f1ed7f4f258f89931209cd7de6030be9f6875372d7329151b822a6ba2281f`, 19,184,103 bytes. The gzip boundary remains byte 10,240. No alternate compression setting was tried.
- The reduced generation root contains 199 original module copies and the three pinned text inputs. All seven retained indexes match byte-for-byte. The original copied files and directory identities remain unchanged. Extra generation outputs stay outside the archive.
- A separate lookup root contains independent, regular, single-link copies of only the 199 modules and seven retained indexes. Filename and dry-run dependency resolution pass for every module. No generated text-index fallback is available.
- All 406 child commands completed successfully with empty stderr. Every modprobe command uses explicit dry-run/show-depends flags, a private root, exact kernel release, and an empty private configuration. No returned command is executed.

The actual isolation probe and seven smoke tests passed before the workload. The result reports exit 0, unchanged inputs, and no timeout. The 582-entry runtime manifest and sandbox policy were unchanged. Both roots, all child outputs, and the earlier failed control remain private. No general archive extraction, module load, or diagnostic image creation occurred.

## Next boundary

The no-change control now clears the archive/index preparation gate. Next, prepare and verify one separate private diagnostic image with 200 modules: retain all 199 original paths, replace ATC, and add DWC3 glue. Permit only reviewed non-builtin index deltas. Preserve both builtin indexes and all unrelated payloads, metadata, links, early bytes, and archive placement. A missing final verification result means an incomplete artifact, not permission to stage it.

Offline control success is not loader acceptance, a hardware test, or proof of rollback execution. Full Gate 4b remains HOLD; D2 and D3 remain separate and unauthorized. Root-only boot images and GRUB were not freshly read. No package, live checkout, cable, or boot action occurred.
