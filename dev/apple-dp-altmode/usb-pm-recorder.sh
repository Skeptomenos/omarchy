#!/bin/bash
set -euo pipefail
export LC_ALL=C
refuse() { printf 'Refused: %s\n' "$1" >&2; exit 64; }
(( EUID != 0 )) || refuse 'run as an unprivileged user'
root=/sys/devices/platform/soc/502280000.usb
count=180
if (( $# == 1 )) && [[ $1 == "--record" ]]; then
  [[ ! -L $root ]] || refuse 'controller root is a symlink'
elif (( $# == 2 )) && [[ $1 == "--sample" && $2 == /* ]]; then
  root=$(realpath -e -- "$2" 2>/dev/null) || refuse 'fixture root does not exist'
  case $root in / | /sys | /sys/* | /proc | /proc/* | /dev | /dev/*) refuse 'fixture must not be a live system tree' ;; esac
  [[ -d $root ]] || refuse 'fixture root is not a directory'
  special=$(find -P "$root" ! -type f ! -type d -print -quit) || refuse 'fixture tree cannot be inspected'
  [[ -z $special ]] || refuse 'fixture contains a symlink or special file'
  count=1
else
  refuse 'expected --record or --sample ABS_FIXTURE_ROOT'
fi
attributes=(devnum idVendor idProduct power/control power/runtime_status power/runtime_active_time power/runtime_suspended_time power/autosuspend_delay_ms power/wakeup power/usb2_hardware_lpm)
shopt -s nullglob
observe() {
  local object=$1 before after state=observed attribute value status relative
  local -a fields=()
  relative=${object#"$root"/}
  [[ $object != "$root" ]] || relative=.
  before=$(stat -c %i -- "$object" 2>/dev/null) || before=
  for attribute in "${attributes[@]}"; do
    value=
    if [[ -z $before ]]; then
      status=unavailable
    elif [[ -L $object/$attribute || ( -e $object/$attribute && ! -f $object/$attribute ) ]]; then
      status=unsafe_type
    elif [[ ! -e $object/$attribute ]]; then
      status=missing
    elif [[ ! -r $object/$attribute ]]; then
      status=unreadable
    elif value=$(cat -- "$object/$attribute" 2>/dev/null); then
      status=ok
    else
      status=unreadable
    fi
    fields+=("$attribute" "$status" "$value")
  done
  after=$(stat -c %i -- "$object" 2>/dev/null) || after=
  if [[ -z $before || $before != "$after" ]]; then
    state=disappeared_or_replaced
    fields=()
    for attribute in "${attributes[@]}"; do fields+=("$attribute" unavailable ""); done
  fi
  jq -cn --arg path "$relative" --arg inode "$before" --arg state "$state" --args '
    {path:$path,inode:(if $inode == "" then null else $inode end),state:$state,
     attributes:($ARGS.positional | . as $fields | [range(0;length;3) as $i |
       {key:$fields[$i],value:{status:$fields[$i+1],value:(if $fields[$i+1] == "ok" then $fields[$i+2] else null end)}}] | from_entries)}
  ' -- "${fields[@]}"
}
for (( sample=1; sample<=count; sample++ )); do
  read -r begin_uptime _ < /proc/uptime
  begin_wall=$(date --utc --iso-8601=ns)
  paths=()
  [[ ! -d $root ]] || paths+=("$root")
  for controller in "$root"/xhci-hcd.*; do
    [[ -d $controller && ! -L $controller ]] || continue
    paths+=("$controller")
    for hub in "$controller"/usb[0-9]*; do
      [[ -d $hub && ! -L $hub && ${hub##*/} =~ ^usb[0-9]+$ ]] || continue
      paths+=("$hub")
      for child in "$hub"/[0-9]*-[0-9]*; do
        [[ -d $child && ! -L $child && ${child##*/} =~ ^[0-9]+-[0-9]+$ ]] || continue
        paths+=("$child")
        for grandchild in "$child"/[0-9]*-[0-9]*; do
          [[ -d $grandchild && ! -L $grandchild && ${grandchild##*/} =~ ^[0-9]+-[0-9]+\.[0-9]+$ ]] || continue
          paths+=("$grandchild")
        done
      done
    done
  done
  objects=$(for object in "${paths[@]}"; do observe "$object" || exit 1; done)
  read -r end_uptime _ < /proc/uptime
  end_wall=$(date --utc --iso-8601=ns)
  jq -cs --argjson sample "$sample" --arg begin_wall "$begin_wall" --arg begin_uptime "$begin_uptime" --arg end_wall "$end_wall" --arg end_uptime "$end_uptime" '
    {schema:"usb-pm-v1",level:"info",sample:$sample,begin:{wall:$begin_wall,uptime_seconds:$begin_uptime},end:{wall:$end_wall,uptime_seconds:$end_uptime},objects:.}
  ' <<< "$objects"
  if (( sample < count )); then
    remaining=$(( 100 - (10#${end_uptime/./} - 10#${begin_uptime/./}) ))
    if (( remaining > 0 )); then sleep "$(printf '%d.%02d' "$((remaining / 100))" "$((remaining % 100))")"; fi
  fi
done
