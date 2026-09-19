echo "Populate the finalized Omarchy Mac signing keyring"

# A successor is required for clients that already marked earlier migrations
# complete. Never remove existing keys or change repository signature policy.
readonly omarchy_mac_signing_key='FBD6874D423C418DDB6D143EECE19CDDE306DBD2'

keyfile=""
if installed=$(pacman -Q omarchy-mac-keyring); then
  version=${installed#* }
  comparison=$(vercmp "$version" 20260914-2) || exit 1
  if (( comparison < 0 )); then
    echo "Omarchy Mac keyring 20260914-2 or newer is required." >&2
    exit 1
  fi

  sudo pacman-key --populate omarchy-mac || {
    echo "Could not populate Omarchy Mac signing trust; this migration remains pending." >&2
    exit 1
  }
else
  # Edge/git-linked ARM hosts may still have no packaged keyring. Apply the
  # pinned checkout fallback even when their bootstrap marker already exists.
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
