echo "Install missing headers for the Omarchy or T2 kernel"

# These packages are x86-only, even if a stale package record exists on ARM.
[[ $(uname -m) == "x86_64" ]] || exit 0

# Fresh ISO installs mark earlier migrations complete, so the kernel migration
# cannot repair headers omitted by those installers. Package installation is
# idempotent when another user has already applied this repair.
for kernel in linux-omarchy linux-t2; do
  if omarchy-pkg-present "$kernel"; then
    omarchy-pkg-add "$kernel-headers"
  fi
done
