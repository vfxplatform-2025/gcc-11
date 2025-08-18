#!/bin/bash
set -e

# 현재 디렉토리에서 gcc 버전 파싱 (ex: gcc-11.5.0 → 11.5.0)
VER=$(basename "$(pwd)" | sed 's/gcc-//')
cd source

ARCHIVE="gcc-${VER}.tar.xz"
DIR="gcc-${VER}"

# 아카이브 다운로드
if [ ! -f "$ARCHIVE" ]; then
    echo "📦 Downloading $ARCHIVE"
    wget "https://ftp.gnu.org/gnu/gcc/gcc-${VER}/${ARCHIVE}"
else
    echo "✅ Archive already exists: $ARCHIVE"
fi

# 디렉토리 존재 시 삭제 후 재추출
if [ -d "$DIR" ]; then
    echo "⚠️ Removing existing source directory: $DIR"
    rm -rf "$DIR"
fi

echo "📂 Extracting $ARCHIVE"
tar -xf "$ARCHIVE"

# prerequisites 다운로드
echo "🔧 Downloading prerequisites (gmp, mpfr, mpc...)"
cd "$DIR"
./contrib/download_prerequisites

echo "✅ GCC ${VER} source ready."

