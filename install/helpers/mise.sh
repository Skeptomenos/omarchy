#!/bin/bash

omarchy_is_arm_mise_package() {
  local package="${1:-}"

  [[ $(uname -m) == "aarch64" && ( $package == "mise" || $package == "mise-bin" ) ]]
}

omarchy_filter_mise_packages_for_arch() {
  local package

  for package in "$@"; do
    if ! omarchy_is_arm_mise_package "$package"; then
      printf '%s\n' "$package"
    fi
  done
}

omarchy_ensure_arm_mise() (
  if command -v mise >/dev/null 2>&1 && mise --version >/dev/null 2>&1; then
    return 0
  fi

  local version="${OMARCHY_MISE_VERSION:-2026.8.6}"
  local checksum="${OMARCHY_MISE_SHA256:-f9bd051912beb8861bf248289bfb2d8c281ff00fcdf1e44d730b8ea7e859e9a4}"
  local url="${OMARCHY_MISE_URL:-https://github.com/jdx/mise/releases/download/v${version}/mise-v${version}-linux-arm64}"
  local download actual

  if ! command -v curl >/dev/null 2>&1; then
    if ! sudo pacman -S --needed --noconfirm curl; then
      echo "Could not install curl for the ARM mise bootstrap." >&2
      return 1
    fi
  fi
  if ! command -v sha256sum >/dev/null 2>&1; then
    echo "sha256sum is required to verify the ARM mise binary." >&2
    return 1
  fi

  download=$(mktemp) || return 1
  trap 'rm -f "$download"' EXIT

  echo "Installing the verified ARM mise binary (v$version)"
  if ! curl --fail --location --retry 3 --silent --show-error "$url" -o "$download"; then
    echo "Could not download mise from $url." >&2
    return 1
  fi
  actual=$(sha256sum "$download" | awk '{print $1}')
  if [[ $actual != $checksum ]]; then
    echo "mise checksum mismatch: expected $checksum, got $actual." >&2
    return 1
  fi

  if ! sudo install -Dm0755 "$download" /usr/local/bin/mise; then
    echo "Could not install the verified ARM mise binary." >&2
    return 1
  fi
  if ! command -v mise >/dev/null 2>&1 || ! mise --version >/dev/null 2>&1; then
    echo "The verified ARM mise binary was installed but does not run." >&2
    return 1
  fi
)

omarchy_ensure_mise_for_arch() {
  if [[ $(uname -m) == "aarch64" ]]; then
    omarchy_ensure_arm_mise
  fi
}
