#!/usr/bin/env bash
set -euo pipefail
TARGET_USER="${1:-onlogic}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: su root; ./scripts/setup_permissions.sh onlogic"
  exit 1
fi

groupadd gpio || true
usermod -aG gpio,video,dialout "$TARGET_USER" || true
chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/webinar"

cat > /etc/udev/rules.d/99-gpio.rules <<'RULE'
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
RULE

udevadm control --reload-rules || true
udevadm trigger || true
chgrp gpio /dev/gpiochip* 2>/dev/null || true
chmod 660 /dev/gpiochip* 2>/dev/null || true

echo "Done. Log out and SSH back in so group membership applies."
