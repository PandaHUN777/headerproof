#!/usr/bin/env sh
set -eu

REPO=${HEADERPROOF_REPO:-TayfurYldz/headerproof}
VERSION=${HEADERPROOF_VERSION:-latest}

if ! command -v curl >/dev/null 2>&1; then
    echo "headerproof: curl is required" >&2
    exit 1
fi

case "$(uname -s)" in
    Linux) OS=linux ;;
    Darwin) OS=darwin ;;
    MINGW*|MSYS*|CYGWIN*) OS=windows ;;
    *) echo "headerproof: unsupported OS: $(uname -s)" >&2; exit 1 ;;
esac

case "$(uname -m)" in
    x86_64|amd64) ARCH=amd64 ;;
    arm64|aarch64) ARCH=arm64 ;;
    *) echo "headerproof: unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

if [ "$OS" = "windows" ] && [ "$ARCH" != "amd64" ]; then
    echo "headerproof: Windows arm64 binary is not published" >&2
    exit 1
fi

EXT=""
[ "$OS" = "windows" ] && EXT=".exe"
ASSET="headerproof-${OS}-${ARCH}${EXT}"

if [ "$VERSION" = "latest" ]; then
    BASE_URL="https://github.com/${REPO}/releases/latest/download"
else
    BASE_URL="https://github.com/${REPO}/releases/download/${VERSION}"
fi
BASE_URL=${HEADERPROOF_BASE_URL:-$BASE_URL}

TMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t headerproof)
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM

curl -fL --retry 3 -o "$TMP_DIR/$ASSET" "$BASE_URL/$ASSET"
curl -fL --retry 3 -o "$TMP_DIR/checksums.txt" "$BASE_URL/checksums.txt"

EXPECTED=$(awk -v file="$ASSET" '$2 == file {print $1}' "$TMP_DIR/checksums.txt")
if [ -z "$EXPECTED" ]; then
    echo "headerproof: checksum entry missing for $ASSET" >&2
    exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL=$(sha256sum "$TMP_DIR/$ASSET" | awk '{print $1}')
else
    ACTUAL=$(shasum -a 256 "$TMP_DIR/$ASSET" | awk '{print $1}')
fi

if [ "$EXPECTED" != "$ACTUAL" ]; then
    echo "headerproof: checksum verification failed" >&2
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    BIN_DIR=${HEADERPROOF_BIN_DIR:-/usr/local/bin}
else
    BIN_DIR=${HEADERPROOF_BIN_DIR:-"$HOME/.local/bin"}
fi
mkdir -p "$BIN_DIR"
TARGET="$BIN_DIR/headerproof${EXT}"
cp "$TMP_DIR/$ASSET" "$TARGET"
chmod 755 "$TARGET" 2>/dev/null || true

echo "headerproof: installed $TARGET"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "headerproof: add $BIN_DIR to PATH" >&2 ;;
esac
