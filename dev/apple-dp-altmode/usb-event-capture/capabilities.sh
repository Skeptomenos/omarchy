#!/bin/bash
set -u -o pipefail
export LC_ALL=C

if (( $# != 0 )); then
  printf 'REFUSED arguments\n'
  exit 64
fi
if (( EUID != 0 )); then
  printf 'REFUSED root_required\n'
  exit 77
fi

readonly trace_root=/sys/kernel/tracing
readonly file_limit=16384
inventory_status=0
paths=(trace_clock current_tracer tracing_on)
for event in rpm_suspend rpm_resume rpm_status rpm_return_int; do paths+=("events/rpm/$event/format"); done
for event in xhci_urb_enqueue xhci_urb_dequeue xhci_urb_giveback xhci_queue_trb xhci_handle_transfer xhci_handle_port_status; do paths+=("events/xhci-hcd/$event/format"); done
for event in usb_alloc_dev usb_set_device_state; do paths+=("events/usbcore/$event/format"); done

check_path() {
  local path=$1 component prefix= parts
  IFS=/ read -r -a parts <<< "$path"
  for component in "${parts[@]}"; do
    [[ -n $component ]] || continue
    prefix+=/$component
    if [[ -L $prefix ]]; then
      file_status=unsafe_symlink
      return
    elif [[ ! -e $prefix ]]; then
      file_status=missing
      return
    elif [[ $prefix != "$path" && ! -d $prefix ]]; then
      file_status=unsafe_type
      return
    fi
  done
  if [[ ! -f $path ]]; then
    file_status=unsafe_type
  elif [[ ! -r $path ]]; then
    file_status=unreadable
  fi
}

kernel_release=$(/usr/bin/timeout --kill-after=1s 1s /usr/bin/uname -r)
kernel_status=$?
printf 'FORMAT dev147-trace-capabilities-v1\nKERNEL %s\n' "$kernel_release"
if (( kernel_status != 0 )); then
  printf 'KERNEL_STATUS error_%s\n' "$kernel_status"
  inventory_status=1
fi

for relative in "${paths[@]}"; do
  path=$trace_root/$relative
  file_status=complete
  encoded=
  bytes=0
  check_path "$path"
  if [[ $file_status == "complete" ]]; then
    encoded=$(/usr/bin/timeout --kill-after=1s 1s /usr/bin/head -c "$((file_limit + 1))" -- "$path" | /usr/bin/base64 -w 0)
    read_status=$?
    if (( read_status != 0 )); then
      file_status=read_error_$read_status
      encoded=
    else
      bytes=$((${#encoded} / 4 * 3))
      if [[ $encoded == *== ]]; then
        (( bytes -= 2 ))
      elif [[ $encoded == *= ]]; then
        (( bytes -= 1 ))
      fi
      if (( bytes > file_limit )); then
        file_status=truncated
        bytes=$file_limit
      fi
    fi
  fi
  printf 'BEGIN %s\nSTATUS %s\nBYTES %s\n' "$path" "$file_status" "$bytes"
  if [[ -n $encoded ]]; then
    if ! printf '%s' "$encoded" | /usr/bin/base64 -d | /usr/bin/head -c "$file_limit"; then
      printf '\nOUTPUT_ERROR\n'
      inventory_status=1
    fi
  fi
  printf '\nEND %s\n' "$path"
  [[ $file_status == "complete" ]] || inventory_status=1
done

if (( inventory_status == 0 )); then
  printf 'INVENTORY complete\n'
else
  printf 'INVENTORY incomplete\n'
fi
exit "$inventory_status"
