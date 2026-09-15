echo "Trust packages signed by Omarchy Mac"

readonly omarchy_mac_signing_key='F3C5AE3FCFFC738C301E30A8F0C548C0D27279F7'

# The package is a dependency of omarchy, but keep this self-repairing for a
# partial/manual upgrade. Do not weaken the repository policy to fetch it.
if omarchy-pkg-missing omarchy-mac-keyring; then
  omarchy-pkg-add omarchy-mac-keyring
fi

if omarchy-pkg-present omarchy-mac-keyring; then
  sudo pacman-key --populate omarchy-mac
else
  # ARM pkg-add skips packages with no repo; git-linked machines also have no
  # packaged files under /usr/share/pacman/keyrings. Import the pinned public
  # bytes from this checkout, the same way the Apple Silicon installer does.
  keyfile="$OMARCHY_PATH/default/pacman/keyrings/omarchy-mac.gpg"
  [[ -f $keyfile && ! -L $keyfile ]] || {
    echo "Pinned Omarchy Mac signing key is missing or unsafe: $keyfile" >&2
    exit 1
  }
  sudo pacman-key --add "$keyfile"
  sudo pacman-key --lsign-key "$omarchy_mac_signing_key"
fi

sudo pacman-key --finger "$omarchy_mac_signing_key" | tr -d '[:space:]' | grep -qF "$omarchy_mac_signing_key"

# Policy remains unchanged for this one disclosed bootstrap transaction. The
# next, signed RC carries a successor migration that requires both package and
# database signatures after this key is already durable.
