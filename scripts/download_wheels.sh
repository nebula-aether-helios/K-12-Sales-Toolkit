#!/usr/bin/env bash
set -euo pipefail

# Download Python wheels for offline installation
# Usage: run this on a machine with network access
#   ./scripts/download_wheels.sh [-r requirements.txt] [-d vendor_wheels]

REQ=${1:-requirements.txt}
DEST=${2:-vendor_wheels}

if [ ! -f "$REQ" ]; then
  echo "Requirements file $REQ not found" >&2
  exit 1
fi

mkdir -p "$DEST"
echo "Downloading wheels from PyPI into $DEST (this requires network access)" 
pip download -r "$REQ" -d "$DEST"
echo "Done. Copy the $DEST directory to the offline machine and run the bootstrap script there."
