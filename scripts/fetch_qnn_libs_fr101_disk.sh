#!/usr/bin/env bash
set -euo pipefail
ZIP_FILE=""
DOWNLOAD_URL=""
INSTALL_DIR="/home/onlogic/webinar/qairt-runtime"
WORK_BASE="/home/onlogic/webinar/tmp"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --zip-file) ZIP_FILE="$2"; shift 2 ;;
    --download-url) DOWNLOAD_URL="$2"; shift 2 ;;
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --work-base) WORK_BASE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$ZIP_FILE" && -z "$DOWNLOAD_URL" ]]; then
  echo "Provide --zip-file or --download-url"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
INSTALL_DIR="$(realpath -m "$INSTALL_DIR")"
WORK_BASE="$(realpath -m "$WORK_BASE")"
mkdir -p "$WORK_BASE" "$INSTALL_DIR"
WORKDIR="$(mktemp -d "$WORK_BASE/qairt-work.XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT
ZIP_PATH="$WORKDIR/qairt.zip"
EXTRACT_DIR="$WORKDIR/extract"
mkdir -p "$EXTRACT_DIR"

echo "[INFO] Workdir: $WORKDIR"
echo "[INFO] Install dir: $INSTALL_DIR"
echo "[1/8] Preparing QAIRT zip"
if [[ -n "$ZIP_FILE" ]]; then
  [[ -f "$ZIP_FILE" ]] || { echo "Zip not found: $ZIP_FILE"; exit 1; }
  ZIP_PATH="$(realpath "$ZIP_FILE")"
else
  if command -v curl >/dev/null 2>&1; then
    curl -fL -o "$ZIP_PATH" "$DOWNLOAD_URL"
  else
    wget -O "$ZIP_PATH" "$DOWNLOAD_URL"
  fi
fi

echo "[2/8] Testing zip"
unzip -t "$ZIP_PATH" >/dev/null

echo "[3/8] Extracting only runtime libraries, not full SDK"
unzip -q "$ZIP_PATH" \
  "*/lib/aarch64-ubuntu-gcc*/*.so" \
  "*/lib/hexagon-v68/unsigned/*.so" \
  "*/bin/aarch64-ubuntu-gcc*/qnn-platform-validator" \
  -d "$EXTRACT_DIR" || true

LINUX_LIB_DIR="$INSTALL_DIR/lib/aarch64-ubuntu-gcc9.4"
HEXAGON_LIB_DIR="$INSTALL_DIR/lib/hexagon-v68/unsigned"
BIN_DIR="$INSTALL_DIR/bin/aarch64-ubuntu-gcc9.4"
mkdir -p "$LINUX_LIB_DIR" "$HEXAGON_LIB_DIR" "$BIN_DIR"

mapfile -t LINUX_SO_FILES < <(find "$EXTRACT_DIR" -type f -name "*.so" | grep -E "/lib/aarch64-ubuntu-gcc[0-9.]+/" || true)
mapfile -t HEXAGON_SO_FILES < <(find "$EXTRACT_DIR" -type f -name "*.so" | grep -E "/lib/hexagon-v68/unsigned/" || true)
mapfile -t VALIDATORS < <(find "$EXTRACT_DIR" -type f -name "qnn-platform-validator" || true)

if [[ "${#LINUX_SO_FILES[@]}" -eq 0 ]]; then
  echo "No Linux AARCH64 QAIRT libraries found. Inspect with: unzip -l $ZIP_PATH | grep libQnnTFLiteDelegate.so"
  exit 1
fi
for file in "${LINUX_SO_FILES[@]}"; do cp -f "$file" "$LINUX_LIB_DIR/"; done
for file in "${HEXAGON_SO_FILES[@]}"; do cp -f "$file" "$HEXAGON_LIB_DIR/"; done
if [[ "${#VALIDATORS[@]}" -gt 0 ]]; then cp -f "${VALIDATORS[0]}" "$BIN_DIR/"; chmod +x "$BIN_DIR/qnn-platform-validator"; fi

cat > "$SCRIPT_DIR/qairt-env.sh" <<ENV
#!/usr/bin/env bash
export QAIRT_RUNTIME_DIR="$INSTALL_DIR"
export LD_LIBRARY_PATH="$LINUX_LIB_DIR:\${LD_LIBRARY_PATH:-}"
export ADSP_LIBRARY_PATH="$HEXAGON_LIB_DIR:\${ADSP_LIBRARY_PATH:-}"
echo "QAIRT_RUNTIME_DIR=\$QAIRT_RUNTIME_DIR"
echo "LD_LIBRARY_PATH=\$LD_LIBRARY_PATH"
echo "ADSP_LIBRARY_PATH=\$ADSP_LIBRARY_PATH"
ENV
chmod +x "$SCRIPT_DIR/qairt-env.sh"

echo "Done. Run: source /home/onlogic/webinar/qairt-env.sh"
for required in libQnnTFLiteDelegate.so libQnnSystem.so libQnnHtp.so; do
  [[ -f "$LINUX_LIB_DIR/$required" ]] && echo "Found: $required" || echo "Missing: $required"
done
