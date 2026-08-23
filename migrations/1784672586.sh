echo "Switch to the Omarchy quickshell-git build so shell restarts wait for instance exit"

if grep -qxF quickshell-git "$OMARCHY_PATH/install/omarchy-base.packages" &&
  ! omarchy-pkg-present quickshell-git; then
  # One transaction with --ask 4 so pacman accepts replacing the conflicting
  # quickshell package in place; packages depending on quickshell stay
  # satisfied through the provides.
  sudo pacman -S --noconfirm --ask 4 quickshell-git
fi
