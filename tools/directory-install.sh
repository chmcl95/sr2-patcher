#!/usr/bin/env bash
# directory-install.sh - install net/directory.py as a systemd service.
#
#   sudo tools/directory-install.sh install [PORT]   default 47627
#   sudo tools/directory-install.sh update           reinstall from this checkout
#   sudo tools/directory-install.sh remove
#          tools/directory-install.sh status
#
# Installs to /opt/sr2-netplay as sr2-directory.service, or PREFIX if set.
# Needs systemd and python3; the
# firewall is left alone and the command to open the port is printed.

set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(dirname "$HERE")
PREFIX=${PREFIX:-/opt/sr2-netplay}
NAME=sr2-directory
UNIT=/etc/systemd/system/$NAME.service

die() { echo "$*" >&2; exit 1; }

need_root() { [ "$(id -u)" = 0 ] || die "run this with sudo"; }

checks() {
    command -v systemctl >/dev/null || die "no systemd on this machine"
    command -v python3 >/dev/null || die "python3 is not installed"
    [ -f "$REPO/net/directory.py" ] || die "run this from a sr2-patcher checkout"
    python3 -c 'import sys; sys.exit(sys.version_info < (3, 6))' \
        || die "python3 is too old"
}

install_files() {
    local port=$1
    install -d -m 755 "$PREFIX"
    install -m 644 "$REPO/net/directory.py" "$PREFIX/directory.py"
    sed -e "s|/opt/sr2-netplay/directory.py 47627|$PREFIX/directory.py $port|" \
        -e "s|UDP 47627|UDP $port|" \
        "$REPO/net/directory.service" > "$UNIT"
    systemctl daemon-reload
}

firewall_hint() {
    local port=$1
    echo
    echo "Open UDP $port, and in any firewall your host runs in front of this box:"
    if command -v ufw >/dev/null; then
        echo "  ufw allow $port/udp comment 'SR2 session directory'"
    elif command -v firewall-cmd >/dev/null; then
        echo "  firewall-cmd --add-port=$port/udp --permanent && firewall-cmd --reload"
    else
        echo "  (no ufw or firewalld found; use whatever this machine has)"
    fi
}

case "${1:-}" in
install)
    need_root
    checks
    port=${2:-47627}
    [ "$port" -gt 0 ] 2>/dev/null && [ "$port" -lt 65536 ] || die "bad port: $port"
    install_files "$port"
    systemctl enable --now "$NAME"
    sleep 2
    systemctl is-active --quiet "$NAME" \
        || die "it did not start; journalctl -u $NAME"
    echo "listening on udp/$port"
    firewall_hint "$port"
    ;;
update)
    need_root
    checks
    [ -f "$UNIT" ] || die "not installed yet"
    port=$(sed -n 's/.*directory\.py \([0-9]*\).*/\1/p' "$UNIT")
    install_files "${port:-47627}"
    systemctl restart "$NAME"
    echo "updated, still on udp/${port:-47627}"
    ;;
remove)
    need_root
    systemctl disable --now "$NAME" 2>/dev/null || true
    rm -f "$UNIT" "$PREFIX/directory.py"
    rmdir "$PREFIX" 2>/dev/null || true
    systemctl daemon-reload
    echo "removed"
    ;;
status)
    systemctl status "$NAME" --no-pager | head -4 || true
    echo
    python3 "$PREFIX/directory.py" status
    ;;
*)
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
    ;;
esac
