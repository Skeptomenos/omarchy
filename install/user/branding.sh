#!/bin/bash

# Seed package-owned branding for users created before the Omarchy defaults
# were installed. Do not replace custom branding or broken symlinks.

set -euo pipefail

branding_dir="$HOME/.config/omarchy/branding"
mkdir -p "$branding_dir"

ensure_default_branding() {
  local source_file="$1"
  local target_file="$2"

  if [[ ! -e $target_file && ! -L $target_file && -f $source_file ]]; then
    install -m 0644 "$source_file" "$target_file"
  fi
}

ensure_default_branding "$OMARCHY_PATH/icon.txt" "$branding_dir/about.txt"
ensure_default_branding "$OMARCHY_PATH/logo.txt" "$branding_dir/screensaver.txt"
