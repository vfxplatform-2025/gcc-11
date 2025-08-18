# -*- coding: utf-8 -*-
name      = "gcc"
version   = "11.5.0"
build_requires = [
    "binutils-2.40",
    "glibc-2.35",
]
variants  = [["platform_linux"]]

build_command = "python {root}/rezbuild.py install"

def commands():
    # 빌드된 binutils/ld/as/gcc-ar 등 우선
    env.PATH.prepend("{REZ_BINUTILS_ROOT}/bin")
    # 설치된 Glibc 라이브러리 우선
    env.LD_LIBRARY_PATH.prepend("{REZ_GLIBC_ROOT}/lib")
    env.LD_LIBRARY_PATH.prepend("{REZ_GLIBC_ROOT}/lib64")
    # 런타임에 사용할 dynamic linker 지정
    env.LD = "{REZ_BINUTILS_ROOT}/bin/ld"
    env.DYNAMIC_LINKER = "{REZ_GLIBC_ROOT}/lib64/ld-linux-x86-64.so.2"
    # GCC 컴파일러 바이너리 설정
    env.CC = "{root}/bin/gcc"
    env.CXX = "{root}/bin/g++"
    env.FC = "{root}/bin/gfortran"

