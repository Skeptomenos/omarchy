#!/bin/bash
set -euo pipefail
[[ $# == 0 ]] || exit 2
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$script_dir/validate-build.sh"
root=/home/david/Work/dev147-clear-wait-trial
release=7.1.12-dev147-clearwait100
commit=d2f36591abdb0db296ac24e5a2b9dade5ae40ef1
base=b8810ad6442699f610984f3eceea2e3234a50b77
candidate="$root/artifacts/candidate-$release"
module_root="$root/artifacts/root/lib/modules/$release"
umask 077
[[ $(git -C "$root/linux" rev-parse HEAD) == "$commit" ]]
[[ -z $(git -C "$root/linux" status --porcelain) ]]
[[ $(cat "$root/build/include/config/kernel.release") == "$release" ]]
printf '%s  %s\n' f69e63e55cbc6b257a951c82b3e581ffc60d4614a5965561cbc322960767bdff "$root/build/.config" | sha256sum --check --strict
for artifact in arch/arm64/boot/Image arch/arm64/boot/dts/apple/t8112-j413.dtb System.map Module.symvers modules.order; do
  [[ -s $root/build/$artifact ]]
done
verify_module_tree "$root/build" "$module_root"
[[ -s $module_root/modules.dep ]]
mkdir "$candidate"
cp "$root/build/arch/arm64/boot/Image" "$candidate/Image"
cp "$root/build/arch/arm64/boot/dts/apple/t8112-j413.dtb" "$candidate/t8112-j413.dtb"
cp "$root/build/.config" "$candidate/config"
cp "$root/build/System.map" "$root/build/Module.symvers" "$root/build/modules.order" "$candidate/"
cp "$root/build-command.sh" "$candidate/build-command.sh"
printf '%s\n' "$release" > "$candidate/kernelrelease.txt"
printf '%s\n' "$commit" > "$candidate/source-commit.txt"
printf '%s\n' "$base" > "$candidate/bundle-base.txt"
git -C "$root/linux" format-patch --no-signature --output-directory "$candidate" "$base..$commit"
git -C "$root/linux" bundle create "$candidate/source.bundle" "$base..HEAD"
git -C "$root/linux" bundle verify "$candidate/source.bundle"
(
  cd "$root/artifacts/root"
  find "lib/modules/$release" -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$candidate/modules.sha256"
)
(
  cd "$candidate"
  find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%P\0' | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
  sha256sum --check --strict SHA256SUMS
)
printf 'ASSEMBLED: %s; run validate-build.sh before accepting the offline build.\n' "$candidate"
