# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고할 가이드입니다.

**Always answer in Korean.**

## 저장소 개요

이 저장소는 Rez 패키지 관리를 사용하는 M83 툴체인용 GCC 11.5.0 빌드 구성을 포함합니다. 주요 목표는 적절한 시스템 헤더(stdlib.h 등)가 포함된 GCC를 빌드하는 것입니다.

## 중요한 빌드 컨텍스트

### 시스템 헤더 이슈
주요 과제는 GCC가 올바른 C 시스템 헤더와 함께 빌드되도록 하는 것입니다. 빌드 구성에는 stdlib.h와 같은 표준 C 헤더를 포함하기 위해 적절한 `--with-sysroot`와 `--with-native-system-header-dir` 설정이 필요합니다.

### 핵심 파일
- **package.py**: Rez 패키지 정의, GCC 도구 내보내기 및 환경 변수 설정
- **rezbuild.py**: rez-build 명령용 메인 빌드 스크립트
- **build.sh**: GMP 패치와 sysroot 구성이 포함된 독립 실행형 빌드 스크립트

### 참조 빌드 위치
성공적으로 빌드된 참조 위치: `/core/Linux/APPZ/packages/_gcc/11.5.0/platform_linux`
- C++ 헤더, 라이브러리, 바이너리가 포함된 완전한 GCC 설치

## 빌드 명령어

### 표준 Rez 빌드
```bash
rez-build -i
```

### 직접 빌드 스크립트 (sysroot 포함)
```bash
./build.sh
```

### 수동 빌드 프로세스
```bash
# 환경 설정
export REZ_BUILD_SOURCE_PATH=$(pwd)
export REZ_BUILD_PATH=$(pwd)/.rez_build
export REZ_BUILD_PROJECT_VERSION=11.5.0
export REZ_BUILD_INSTALL_PATH=/core/Linux/APPZ/packages/gcc/${REZ_BUILD_PROJECT_VERSION}

# rezbuild.py 실행
python rezbuild.py install
```

## 빌드 구성 상세

### Configure 옵션 (rezbuild.py에서)
```bash
--prefix={install_path}
--enable-languages=c,c++,fortran
--disable-multilib
--enable-shared
--enable-threads=posix
--enable-lto
--enable-__cxa_atexit
--enable-checking=release
--with-system-zlib
--with-pkgversion="M83 GCC 11.5.0 Toolchain"
```

### Sysroot 구성 (build.sh에서)
```bash
--with-sysroot="${REZ_GLIBC_ROOT}"
--with-native-system-header-dir="include"
```

### GMP 패치 필요
build.sh 스크립트는 충돌을 피하기 위해 GMP의 strnlen 함수에 대한 중요한 패치를 포함합니다:
- 위치: `gmp/printf/repl-vsnprintf.c`
- strnlen 정의를 `#ifndef HAVE_STRNLEN`으로 감싸기

## 환경 의존성

### 필수 Rez 패키지
- binutils (어셈블러/링커용)
- glibc (시스템 헤더 및 라이브러리용)

### 빌드 환경 변수
- `REZ_BINUTILS_ROOT`: binutils 설치 경로
- `REZ_GLIBC_ROOT`: glibc 설치 경로 (sysroot로 사용)
- `CPPFLAGS`: 헤더용 포함 경로
- `LDFLAGS`: sysroot가 포함된 링커 플래그

## 디렉토리 구조
```
gcc-11.5.0/
├── source/
│   ├── gcc-11.5.0.tar.xz  # 소스 아카이브
│   └── gcc-11.5.0/        # 추출된 소스
├── .rez_build/            # 빌드 디렉토리 (분석에서 제외)
│   └── gcc-build/         # Configure 및 make 출력
├── package.py             # Rez 패키지 정의
├── rezbuild.py           # 메인 빌드 스크립트
└── build.sh              # 패치가 포함된 대체 빌드 스크립트
```

## 일반적인 문제와 해결 방법

### 시스템 헤더 누락
**문제**: 빌드된 GCC가 stdlib.h 또는 다른 시스템 헤더를 찾지 못함
**해결**: 적절한 sysroot 구성이 포함된 build.sh를 사용하거나 rezbuild.py를 수정하여 추가:
- glibc 설치를 가리키는 `--with-sysroot` 옵션
- `--with-native-system-header-dir`을 "include"로 설정

### GMP strnlen 충돌
**문제**: 중복 strnlen 정의로 인한 빌드 실패
**해결**: build.sh의 패치를 적용하여 GMP의 strnlen을 HAVE_STRNLEN으로 보호

### 빌드 경로
**참고**: `rez-build -i` 사용 시 설치 경로는 `/core/Linux/APPZ/packages/gcc/{version}`으로 하드코딩됨

## 빌드 테스트

빌드 후 설치에 다음 항목이 포함되어 있는지 확인:
1. 시스템 헤더: `{install_path}/include/c++/11.5.0/`에서 C++ 헤더 확인
2. 라이브러리: `{install_path}/lib64/`에서 libstdc++, libgcc_s 등 확인
3. 바이너리: `{install_path}/bin/`에서 gcc, g++, gfortran 확인
4. 컴파일러가 시스템 헤더와 작동하는지 확인: `echo '#include <stdlib.h>' | {install_path}/bin/gcc -E -`