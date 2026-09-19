echo "Install Elsewhen, the world clock plugin"

omarchy-pkg-add elsewhen

# ARM package installation can skip an unavailable package with exit status 0.
if ! omarchy-pkg-present elsewhen; then
  echo "Elsewhen is unavailable from the configured package sources; the migration remains pending." >&2
  exit 1
fi

package_plugin=/usr/share/omarchy/plugins/omacom.elsewhen
if [[ ! -f $package_plugin/manifest.json ]]; then
  echo "The Elsewhen package is missing its plugin payload; the migration remains pending." >&2
  exit 1
fi

plugin="$HOME/.config/omarchy/plugins/omacom.elsewhen"
mkdir -p "$(dirname "$plugin")"
if [[ ! -e $plugin && ! -L $plugin ]]; then
  ln -s "$package_plugin" "$plugin"
fi

omarchy-shell shell rescanPlugins
omarchy-bar put omacom.elsewhen --before omarchy.clock
