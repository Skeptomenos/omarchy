echo "Trust packages signed by Omarchy Mac"

readonly omarchy_mac_signing_key='FBD6874D423C418DDB6D143EECE19CDDE306DBD2'

# The package is a dependency of omarchy, but keep this self-repairing for a
# partial/manual upgrade. Do not weaken the repository policy to fetch it.
if omarchy-pkg-missing omarchy-mac-keyring; then
  omarchy-pkg-add omarchy-mac-keyring || exit 1
fi

keyfile=""
if installed_keyring=$(pacman -Q omarchy-mac-keyring); then
  installed_version=${installed_keyring#* }
  version_comparison=$(vercmp "$installed_version" 20260914-2) || exit 1
  if (( version_comparison < 0 )); then
    echo "Omarchy Mac keyring 20260914-2 or newer is required (installed: $installed_version); complete the reviewed RC4 package upgrade before retrying this migration." >&2
    exit 1
  fi

  sudo pacman-key --populate omarchy-mac || {
    echo "Could not populate Omarchy Mac signing trust; this migration remains pending." >&2
    exit 1
  }
else
  # ARM pkg-add skips packages with no repo; git-linked machines also have no
  # packaged files under /usr/share/pacman/keyrings. Verify the checkout's only
  # primary before importing it. Never use this fallback for an older package.
  keyfile="$OMARCHY_PATH/default/pacman/keyrings/omarchy-mac.gpg"
  [[ -f $keyfile && ! -L $keyfile ]] || {
    echo "Pinned Omarchy Mac signing key is missing or unsafe: $keyfile" >&2
    exit 1
  }
  key_info=$(gpg --batch --with-colons --show-keys "$keyfile") || {
    echo "Could not read the pinned Omarchy Mac signing key: $keyfile" >&2
    exit 1
  }
  if ! awk -F: -v expected="$omarchy_mac_signing_key" '
    $1 == "sec" || $1 == "ssb" { secret = 1 }
    $1 == "pub" { primaries++; primary = 1; next }
    primary && $1 == "fpr" { fingerprint = $10; primary = 0 }
    END { exit (secret || primaries != 1 || fingerprint != expected) }
  ' <<<"$key_info"; then
    echo "Pinned Omarchy Mac key must contain only signing primary $omarchy_mac_signing_key, without secret key records." >&2
    exit 1
  fi
  sudo pacman-key --add "$keyfile" || {
    echo "Could not import the pinned Omarchy Mac signing key; this migration remains pending." >&2
    exit 1
  }
fi

if ! sudo pacman-key --finger "$omarchy_mac_signing_key" | tr -d '[:space:]' | grep -qF "$omarchy_mac_signing_key"; then
  echo "The required Omarchy Mac signing primary $omarchy_mac_signing_key is missing after keyring population or import." >&2
  exit 1
fi
if [[ -n $keyfile ]]; then
  sudo pacman-key --lsign-key "$omarchy_mac_signing_key" || {
    echo "Could not locally sign the pinned Omarchy Mac signing key; this migration remains pending." >&2
    exit 1
  }
fi

# Policy remains unchanged for this one disclosed bootstrap transaction. The
# next, signed RC carries a successor migration that requires both package and
# database signatures after this key is already durable.
