echo "Apply and verify the packaged BBR and fq network defaults"

# The old ARM package omitted BBR/fq, so 1789444042 could complete after
# loading only MTU probing. Do not overwrite administrator edits or a .pacnew.
config=/etc/sysctl.d/99-omarchy-sysctl.conf
values=$(sysctl --dry-run --pattern '^net[./]' --load "$config")
if ! awk '
  $2 == "=" { values[$1] = $3 }
  END { exit !(values["net.ipv4.tcp_mtu_probing"] == "1" &&
    values["net.core.default_qdisc"] == "fq" &&
    values["net.ipv4.tcp_congestion_control"] == "bbr") }
' <<<"$values"; then
  echo "Expected MTU probing=1, qdisc=fq and congestion control=bbr in $config." >&2
  echo "Update omarchy-settings and review any .pacnew while preserving local edits, then retry." >&2
  exit 1
fi

network_defaults_applied() {
  [[ $(sysctl -n net.ipv4.tcp_mtu_probing) == "1" &&
    $(sysctl -n net.core.default_qdisc) == "fq" &&
    $(sysctl -n net.ipv4.tcp_congestion_control) == "bbr" ]]
}

if ! network_defaults_applied; then
  # Limit this repair to network settings, including in locally edited files.
  # Existing sockets and attached qdiscs still need reconnection or reboot.
  sudo sysctl --pattern '^net[./]' --load "$config" >/dev/null
  if ! network_defaults_applied; then
    echo "Network defaults did not take effect; leaving this migration pending." >&2
    exit 1
  fi
fi
