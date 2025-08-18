#!/usr/bin/env bash
# build.sh — GCC 11.5.0 Toolchain 완전 독립 빌드/설치 (with clean & sed patch)
set -euo pipefail

#
# 1) Rez 빌드 환경변수 기본값 선언
#
: "${REZ_BUILD_SOURCE_PATH:=$(pwd)}"
: "${REZ_BUILD_PATH:=$(pwd)/.rez_build}"
: "${REZ_BUILD_PROJECT_VERSION:=11.5.0}"
: "${REZ_BUILD_INSTALL_PATH:=/core/Linux/APPZ/packages/gcc/${REZ_BUILD_PROJECT_VERSION}}"

#
# 2) 이전 빌드 디렉터리 및 로그 완전 삭제 (깨끗한 재빌드)
#
rm -rf "${REZ_BUILD_PATH}"
rm -f "${HOME}/build_full.log"

#
# 3) 주요 경로 설정
#
SRC_ROOT="${REZ_BUILD_SOURCE_PATH}/source"
BUILD_ROOT="${REZ_BUILD_PATH}"
INSTALL_ROOT="${REZ_BUILD_INSTALL_PATH}"
GCC_SRC_DIR="${SRC_ROOT}/gcc-${REZ_BUILD_PROJECT_VERSION}"

if [[ ! -d "${GCC_SRC_DIR}" ]]; then
  echo "❌ Error: source dir not found → ${GCC_SRC_DIR}"
  exit 1
fi

#
# 4) 빌드 디렉터리 초기화
#
BUILD_DIR="${BUILD_ROOT}/gcc-build"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

#
# 5) GMP 소스 패치: static strnlen 충돌 회피 (autopatch + sed 보완)
#
PATCH_FILE="${GCC_SRC_DIR}/gmp/printf/repl-vsnprintf.c"

# autopatch (patch -p0)
if grep -q "static size_t strnlen" "${PATCH_FILE}"; then
  echo "[INFO] Applying GMP strnlen patch via patch(1)…"
  patch -p0 -d "${GCC_SRC_DIR}" << 'EOF'
*** Begin Patch
*** Update File: gmp/printf/repl-vsnprintf.c
@@
- static size_t
+ /* If system has strnlen(), skip GMP's internal version */
+#ifndef HAVE_STRNLEN
+ static size_t
    strnlen (const char *s, size_t limit)
 {
@@
- }
+ }
+#endif
*** End Patch
EOF
fi

# sed 기반 추가 패치 (보완)
echo "[INFO] Applying GMP strnlen guard via sed…"
sed -i '1i#ifndef HAVE_STRNLEN' "${PATCH_FILE}"
sed -i '/static size_t strnlen/,/^}/ s/^/    /' "${PATCH_FILE}"
sed -i "/^}/a #endif /* HAVE_STRNLEN */" "${PATCH_FILE}"

#
# 6) 최소 툴체인 환경 설정
#    - binutils만 Rez, 컴파일러는 호스트 시스템 사용
#
export PATH="${REZ_BINUTILS_ROOT}/bin:${PATH}"
unset CC CXX LD

# sysroot용 헤더/라이브러리 경로 전달
export CPPFLAGS="-I${REZ_GLIBC_ROOT}/include"
export LDFLAGS="--sysroot=${REZ_GLIBC_ROOT}"

#
# 7) Configure with sysroot & native headers
#
echo "[INFO] Configuring GCC @ ${BUILD_DIR}"
"${GCC_SRC_DIR}/configure" \
  --prefix="${INSTALL_ROOT}" \
  --enable-languages=c,c++,fortran \
  --disable-multilib \
  --enable-shared \
  --enable-threads=posix \
  --enable-lto \
  --enable-__cxa_atexit \
  --enable-checking=release \
  --with-system-zlib \
  --with-sysroot="${REZ_GLIBC_ROOT}" \
  --with-native-system-header-dir="include" \
  --with-pkgversion="M83 GCC ${REZ_BUILD_PROJECT_VERSION} Toolchain"

#
# 8) Build & Install
#
echo "[INFO] Building with $(nproc) cores…"
make -j"$(nproc)"

echo "[INFO] Installing to ${INSTALL_ROOT}…"
make install

echo "✅ GCC ${REZ_BUILD_PROJECT_VERSION} built & installed at ${INSTALL_ROOT}"




#ninja -j$(nproc) -v > ninja.log 2>&1
#grep -i "failed\|undefined\|error\|fatal" ninja.log


