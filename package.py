# -*- coding: utf-8 -*-

name = 'gcc'

version = '11.5.0'

description = "GNU Compiler Collection (M83 Toolchain)"

authors = ['GNU']

tools = [
    'gcc',
    'g++',
    'c++',
    'cpp',
    'gcc-ar',
    'gcc-ranlib',
    'gfortran',
    'gcc-nm',
    'gcov',
    'gcov-dump',
    'gcov-tool'
]

variants = [['platform_linux']]

build_command = 'python {root}/rezbuild.py {install}'

def commands():
    # Rez가 variant를 자동으로 추가하므로 root만 사용
    gcc_root = "{root}"
    
    # PATH 설정 (prepend로 우선순위 높이기)
    env.PATH.prepend(gcc_root + "/bin")
    
    # 라이브러리 경로 설정
    env.LD_LIBRARY_PATH.prepend(gcc_root + "/lib64")
    env.LD_LIBRARY_PATH.prepend(gcc_root + "/lib")
    
    # 컴파일러 환경 변수 설정
    if building:
        env.CC = gcc_root + "/bin/gcc"
        env.CXX = gcc_root + "/bin/g++"
        env.FC = gcc_root + "/bin/gfortran"
        env.F77 = gcc_root + "/bin/gfortran"
        env.F90 = gcc_root + "/bin/gfortran"

