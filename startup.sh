#!/usr/bin/env bash
# startup.sh — Boot script for ScamShield on Raspberry Pi 4B
# Place in /etc/rc.local or systemd service, or run manually.
#
# Usage:
#   chmod +x startup.sh
#   ./startup.sh
#
# Assumes:
#   - Python 3.13 venv at ~/scamshield/venv
#   - ScamShield repo at ~/scamshield (or adjust SCAMSHIELD_DIR below)
#   - .env file in ~/scamshield/pi/

set -euo pipefail

SCAMSHIELD_DIR="${SCAMSHIELD_DIR:-$HOME/scamshield}"
PI_DIR="$SCAMSHIELD_DIR/pi"
VENV_DIR="$SCAMSHIELD_DIR/venv"
LOG_FILE="/var/log/scamshield.log"

echo "=== ScamShield startup $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG_FILE"

# Activate venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python venv at $VENV_DIR..." | tee -a "$LOG_FILE"
    python3.13 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$PI_DIR/requirements.txt"
fi

source "$VENV_DIR/bin/activate"

# Load .env
if [ -f "$PI_DIR/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PI_DIR/.env"
    set +a
    echo ".env loaded" | tee -a "$LOG_FILE"
else
    echo "WARNING: $PI_DIR/.env not found — env vars must be pre-set" | tee -a "$LOG_FILE"
fi

# Wait for network (ngrok needs internet)
echo "Waiting for network..." | tee -a "$LOG_FILE"
for i in $(seq 1 20); do
    if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
        echo "Network ready (attempt $i)" | tee -a "$LOG_FILE"
        break
    fi
    sleep 2
done

# Initialize DB (idempotent)
echo "Initializing database..." | tee -a "$LOG_FILE"
python "$PI_DIR/db.py" --init

# Run ScamShield
echo "Starting ScamShield main process..." | tee -a "$LOG_FILE"
exec python "$PI_DIR/main.py" 2>&1 | tee -a "$LOG_FILE"
