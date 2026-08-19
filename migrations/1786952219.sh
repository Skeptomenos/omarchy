echo "Ensure mise uses the supported package or verified ARM binary"

# On non-ARM systems, mise-bin carries mise's own release artifacts and takes
# over from Arch's mise, which it both provides and conflicts with. Apple
# Silicon does not adopt an external mise-bin repository here; it keeps using
# the checksum-verified official binary bootstrap shared with fresh installs.
#
# The swap has to happen in one transaction. Removing mise first breaks
# omarchy-zsh and omarchy-fish, which depend on it; the provides is what keeps
# them satisfied when mise-bin lands in the same transaction that drops mise.
#
# omarchy-pkg-add cannot do that swap: pacman answers its own conflict question
# with No under --noconfirm and fails the whole transaction ("unresolvable
# package conflicts detected"). --ask=4 is that one question, answered yes.

if [[ $(uname -m) == "aarch64" ]]; then
  source "$OMARCHY_PATH/install/helpers/mise.sh"
  omarchy_ensure_arm_mise
elif omarchy-pkg-missing mise-bin; then
  sudo pacman -S --noconfirm --ask=4 mise-bin
fi
