#!/bin/bash
set -euo pipefail
umask 077

printf '%s  %s\n' \
  d9aa45da6e009f655a528faca1bcd9eab4e1ab521a9e467476aae8d32bbc087b /inputs/package \
  43b2dd8fac5bfa9e4e456f5f432601210c5ac603b9ccc0b930ba709421e2f2f1 /inputs/signature \
  | /usr/bin/sha256sum --check --strict

/usr/bin/mkdir /work/gpgv
/usr/bin/gpgv --homedir /work/gpgv \
  --keyring /usr/share/pacman/keyrings/archlinuxarm.gpg \
  /inputs/signature /inputs/package

# List authenticated package members only. No extraction or execution here.
/usr/bin/bsdtar -tf /inputs/package
