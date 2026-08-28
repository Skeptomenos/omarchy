#!/bin/bash
set -euo pipefail
umask 077

printf '%s  %s\n' \
  d9aa45da6e009f655a528faca1bcd9eab4e1ab521a9e467476aae8d32bbc087b /inputs/package \
  43b2dd8fac5bfa9e4e456f5f432601210c5ac603b9ccc0b930ba709421e2f2f1 /inputs/signature \
  | /usr/bin/sha256sum --check --strict

/usr/bin/mkdir /work/gpgv
# Decode only the exact pinned public-key file. GPG still authenticates the
# package. This changes representation, not the trusted keys or sandbox policy.
/usr/bin/python3.14 -I -S -B -c '
import base64
import hashlib
from pathlib import Path
import re

raw = Path("/usr/share/pacman/keyrings/archlinuxarm.gpg").read_bytes()
if hashlib.sha256(raw).hexdigest() != "6ce771e853f04a38a5b533cb33e61f877b9b06b58b6db051eb8a15d737a2332f":
    raise SystemExit("STOP: public keyring hash drift")
lines = raw.splitlines()
if (len(lines) < 5 or lines[0] != b"-----BEGIN PGP PUBLIC KEY BLOCK-----"
        or lines[1] != b"" or lines[-1] != b"-----END PGP PUBLIC KEY BLOCK-----"
        or re.fullmatch(rb"=[A-Za-z0-9+/]{4}", lines[-2]) is None):
    raise SystemExit("STOP: unexpected pinned public-key armor")
decoded = base64.b64decode(b"".join(lines[2:-2]), validate=True)
with Path("/work/gpgv/archlinuxarm-public.gpg").open("xb") as stream:
    stream.write(decoded)
print("Decoded pinned public keyring SHA-256:", hashlib.sha256(decoded).hexdigest())
'

/usr/bin/gpgv --homedir /work/gpgv --status-fd 1 \
  --keyring /work/gpgv/archlinuxarm-public.gpg \
  /inputs/signature /inputs/package

# List authenticated members only. No extraction or package execution here.
/usr/bin/bsdtar -tf /inputs/package
