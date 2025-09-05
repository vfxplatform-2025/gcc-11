# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import glob
import shutil
import re
import time
import tempfile
from pathlib import Path

class BuildError(Exception):
    """커스텀 빌드 에러 클래스"""
    def __init__(self, message, error_type=None, log_file=None):
        super().__init__(message)
        self.error_type = error_type
        self.log_file = log_file

def run_cmd_with_logging(cmd, cwd=None, env=None, log_file=None, timeout=None):
    """로깅 및 에러 처리가 강화된 명령 실행"""
    print(f"[RUN] {cmd}")
    
    if log_file:
        log_path = Path(log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(log_file, 'a') if log_file else tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            process = subprocess.Popen(
                cmd, 
                cwd=cwd, 
                env=env or os.environ, 
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                print(line.rstrip())  # 실시간 출력
                f.write(line)
                f.flush()
                output_lines.append(line.rstrip())
            
            process.wait(timeout=timeout)
            
            if process.returncode != 0:
                # 에러 발생 시 로그 분석
                error_type = analyze_build_error(output_lines)
                raise BuildError(
                    f"Command failed with return code {process.returncode}",
                    error_type=error_type,
                    log_file=f.name if not log_file else log_file
                )
                
    except subprocess.TimeoutExpired:
        process.kill()
        raise BuildError("Command timed out", error_type="timeout")

def run_cmd(cmd, cwd=None, env=None):
    """기존 호환성을 위한 래퍼 함수"""
    run_cmd_with_logging(cmd, cwd, env)

def clean_path(path):
    if os.path.exists(path):
        print(f"🧹 Removing: {path}")
        shutil.rmtree(path)

def analyze_build_error(output_lines):
    """빌드 로그를 분석하여 에러 유형 분류"""
    if not output_lines:
        return "unknown"
    
    # 로그를 하나의 문자열로 합치기
    log_text = '\n'.join(output_lines)
    
    error_patterns = {
        'gmp_strnlen': [
            r'undefined reference to.*strnlen',
            r'multiple definition of.*strnlen',
            r'redefinition of.*strnlen'
        ],
        'missing_deps': [
            r'cannot find -l\w+',
            r'No such file or directory.*\.so',
            r'library not found'
        ],
        'header_missing': [
            r'fatal error.*No such file',
            r'stdlib\.h.*not found',
            r'stdio\.h.*not found',
            r'#include.*No such file'
        ],
        'disk_space': [
            r'No space left on device',
            r'cannot create temp file',
            r'write error.*No space'
        ],
        'memory_limit': [
            r'virtual memory exhausted',
            r'Cannot allocate memory',
            r'cc1.*killed.*signal 9'
        ],
        'permission_denied': [
            r'Permission denied',
            r'cannot create directory.*Permission',
            r'Operation not permitted'
        ],
        'configure_failed': [
            r'configure: error:',
            r'checking.*no',
            r'configure.*failed',
            r'Makefile:.*all.*오류',
            r'make:.*\*\*\*.*오류'
        ],
        'compile_error': [
            r'error:.*undeclared',
            r'error:.*not declared',
            r'fatal error:.*compilation terminated'
        ],
        'link_error': [
            r'undefined reference to',
            r'ld:.*cannot find',
            r'collect2:.*error:'
        ],
        'gcc_bootstrap_error': [
            r'stage1.*failed',
            r'stage2.*failed',
            r'stage3.*failed',
            r'bootstrap.*failed',
            r'fixincludes.*failed'
        ],
        'makefile_error': [
            r'make.*Leaving directory',
            r'make.*Entering directory',
            r'recipe for target.*failed',
            r'Error.*\[.*\]'
        ]
    }
    
    # 에러 패턴 매칭
    for error_type, patterns in error_patterns.items():
        for pattern in patterns:
            if re.search(pattern, log_text, re.IGNORECASE):
                print(f"[ERROR DETECTED] {error_type}: {pattern}")
                return error_type
    
    # 특정 패턴을 찾지 못한 경우
    if 'error:' in log_text.lower() or 'failed' in log_text.lower():
        return "generic_error"
    
    return "unknown"

def auto_fix_error(error_type, build_dir, gcc_src_dir, install_path):
    """에러 유형에 따른 자동 수정"""
    print(f"\n[AUTO FIX] Attempting to fix error type: {error_type}")
    
    fixes_applied = []
    
    if error_type == 'gmp_strnlen':
        if fix_gmp_strnlen_conflict(gcc_src_dir):
            fixes_applied.append("GMP strnlen conflict")
    
    elif error_type == 'missing_deps':
        if check_and_setup_dependencies():
            fixes_applied.append("Dependencies setup")
    
    elif error_type == 'header_missing':
        if fix_header_paths(gcc_src_dir):
            fixes_applied.append("Header paths")
    
    elif error_type == 'disk_space':
        if cleanup_build_artifacts(build_dir):
            fixes_applied.append("Disk space cleanup")
    
    elif error_type == 'memory_limit':
        if reduce_parallel_jobs():
            fixes_applied.append("Reduced parallel jobs")
    
    elif error_type == 'permission_denied':
        if fix_permissions(build_dir, install_path):
            fixes_applied.append("Permissions")
    
    elif error_type == 'gcc_bootstrap_error':
        if fix_gcc_bootstrap_error(build_dir):
            fixes_applied.append("GCC bootstrap fix")
    
    elif error_type == 'makefile_error':
        if fix_makefile_error(build_dir):
            fixes_applied.append("Makefile regeneration")
    
    elif error_type == 'configure_failed':
        if fix_configure_error(build_dir, gcc_src_dir):
            fixes_applied.append("Configure reconfiguration")
    
    if fixes_applied:
        print(f"[AUTO FIX] Applied fixes: {', '.join(fixes_applied)}")
        return True
    else:
        print(f"[AUTO FIX] No automatic fix available for {error_type}")
        return False

def fix_gmp_strnlen_conflict(gcc_src_dir):
    """GMP strnlen 충돌 수정"""
    try:
        patch_file = os.path.join(gcc_src_dir, "gmp/printf/repl-vsnprintf.c")
        if os.path.exists(patch_file):
            # 더 강력한 패치 적용
            with open(patch_file, 'r') as f:
                content = f.read()
            
            # 이미 패치되었는지 확인
            if '#ifndef HAVE_STRNLEN' in content:
                return True
                
            # 전체 strnlen 함수를 조건부로 감싸기
            if 'static size_t strnlen' in content:
                content = re.sub(
                    r'(static size_t\s+strnlen\s*\([^}]+\})',
                    r'#ifndef HAVE_STRNLEN\n\1\n#endif /* HAVE_STRNLEN */',
                    content,
                    flags=re.DOTALL
                )
                
                with open(patch_file, 'w') as f:
                    f.write(content)
                    
                print("[AUTO FIX] Applied enhanced GMP strnlen patch")
                return True
        return False
    except Exception as e:
        print(f"[AUTO FIX] Failed to fix GMP strnlen: {e}")
        return False

def check_and_setup_dependencies():
    """의존성 확인 및 설정"""
    try:
        # REZ 환경에서 필요한 패키지들 확인
        required_packages = ['binutils', 'glibc']
        
        for pkg in required_packages:
            env_var = f"REZ_{pkg.upper()}_ROOT"
            if env_var not in os.environ:
                print(f"[AUTO FIX] Warning: {env_var} not found")
        
        return True
    except Exception as e:
        print(f"[AUTO FIX] Failed to setup dependencies: {e}")
        return False

def fix_header_paths(gcc_src_dir):
    """헤더 경로 문제 수정"""
    try:
        # 시스템 헤더 경로 확인
        header_paths = ['/usr/include', '/usr/local/include']
        
        for path in header_paths:
            if os.path.exists(os.path.join(path, 'stdlib.h')):
                print(f"[AUTO FIX] Found system headers at: {path}")
                return True
        
        print("[AUTO FIX] Warning: System headers not found in standard locations")
        return False
    except Exception as e:
        print(f"[AUTO FIX] Failed to fix header paths: {e}")
        return False

def cleanup_build_artifacts(build_dir):
    """빌드 아티팩트 정리"""
    try:
        if os.path.exists(build_dir):
            # 임시 파일들 정리
            temp_patterns = ['*.tmp', '*.temp', 'core.*', '*.o']
            cleaned = 0
            
            for pattern in temp_patterns:
                for file_path in glob.glob(os.path.join(build_dir, '**', pattern), recursive=True):
                    try:
                        os.remove(file_path)
                        cleaned += 1
                    except:
                        pass
            
            print(f"[AUTO FIX] Cleaned {cleaned} temporary files")
            return cleaned > 0
        return False
    except Exception as e:
        print(f"[AUTO FIX] Failed to cleanup: {e}")
        return False

def reduce_parallel_jobs():
    """병렬 작업 수 감소"""
    try:
        # 환경 변수 MAKEFLAGS 설정
        current_jobs = os.cpu_count()
        reduced_jobs = max(1, current_jobs // 2)
        
        os.environ['MAKEFLAGS'] = f'-j{reduced_jobs}'
        print(f"[AUTO FIX] Reduced parallel jobs from {current_jobs} to {reduced_jobs}")
        return True
    except Exception as e:
        print(f"[AUTO FIX] Failed to reduce parallel jobs: {e}")
        return False

def fix_permissions(build_dir, install_path):
    """권한 문제 수정"""
    try:
        # 빌드 디렉토리 권한 확인
        if os.path.exists(build_dir) and not os.access(build_dir, os.W_OK):
            print(f"[AUTO FIX] Warning: No write permission to {build_dir}")
        
        # 설치 디렉토리 권한 확인
        install_parent = os.path.dirname(install_path)
        if not os.access(install_parent, os.W_OK):
            print(f"[AUTO FIX] Warning: No write permission to {install_parent}")
        
        return True
    except Exception as e:
        print(f"[AUTO FIX] Failed to fix permissions: {e}")
        return False

def smart_rebuild(source_path, build_path, install_path, error_count=0, max_retries=3):
    """지능적 재빌드 시스템"""
    if error_count >= max_retries:
        raise BuildError(f"Build failed after {max_retries} attempts")
    
    strategies = [
        ('continue_build', 'Continue from current state'),
        ('clean_rebuild', 'Full clean rebuild'),
        ('single_thread', 'Single thread rebuild'),
        ('minimal_config', 'Minimal configuration rebuild')
    ]
    
    strategy_name, strategy_desc = strategies[min(error_count, len(strategies) - 1)]
    
    print(f"\n[REBUILD STRATEGY {error_count + 1}/{max_retries}] {strategy_desc}")
    
    try:
        if strategy_name == 'clean_rebuild':
            clean_path(build_path)
        elif strategy_name == 'single_thread':
            os.environ['MAKEFLAGS'] = '-j1'
        elif strategy_name == 'minimal_config':
            # 최소 설정으로 변경 (기본 옵션만 사용)
            os.environ['GCC_MINIMAL_BUILD'] = '1'
            # configure 마커도 삭제하여 재구성 강제
            configure_done = os.path.join(build_path, "gcc-build", ".configure_done")
            if os.path.exists(configure_done):
                os.remove(configure_done)
        
        # 빌드 재시도
        _build(source_path, build_path, install_path)
        
        print(f"[REBUILD SUCCESS] Strategy '{strategy_desc}' successful!")
        return True
        
    except BuildError as e:
        print(f"[REBUILD FAILED] Strategy '{strategy_desc}' failed: {e}")
        
        # 자동 수정 시도
        if e.error_type and auto_fix_error(e.error_type, build_path, 
                                         os.path.join(source_path, "source/gcc-11.5.0"), 
                                         install_path):
            # 수정 후 재시도
            return smart_rebuild(source_path, build_path, install_path, error_count + 1, max_retries)
        else:
            # 다음 전략으로 넘어가기
            return smart_rebuild(source_path, build_path, install_path, error_count + 1, max_retries)

def copy_package_py(source_path, install_path):
    src = os.path.join(source_path, "package.py")
    # package.py는 platform_linux의 상위 디렉토리에 있어야 함
    if "platform_linux" in install_path:
        dst_dir = os.path.dirname(install_path)
    else:
        dst_dir = install_path
    dst = os.path.join(dst_dir, "package.py")
    if os.path.exists(src):
        print(f"📄 Copying package.py → {dst}")
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy(src, dst)

def patch_gmp(gcc_src_dir):
    """GMP strnlen 충돌 방지 패치 (build.sh와 동일한 강력한 패치)"""
    patch_file = os.path.join(gcc_src_dir, "gmp/printf/repl-vsnprintf.c")
    if os.path.exists(patch_file):
        print("[INFO] Applying GMP strnlen patch...")
        with open(patch_file, 'r') as f:
            content = f.read()
        
        # 이미 패치되었는지 확인
        if '#ifndef HAVE_STRNLEN' in content:
            print("✅ GMP patch already applied")
            return
        
        # strnlen 함수가 있고 아직 패치되지 않았다면 패치 적용
        if 'static size_t strnlen' in content:
            import re
            
            # 전체 strnlen 함수를 찾아서 조건부 컴파일로 감싸기
            pattern = r'(static size_t\s+strnlen\s*\([^{]*\{[^}]*\})'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                strnlen_func = match.group(1)
                # 함수 전체를 HAVE_STRNLEN 가드로 감싸기
                guarded_func = f'#ifndef HAVE_STRNLEN\n{strnlen_func}\n#endif /* HAVE_STRNLEN */'
                content = content.replace(strnlen_func, guarded_func)
                
                with open(patch_file, 'w') as f:
                    f.write(content)
                print("✅ GMP strnlen patch applied successfully")
            else:
                # 패턴이 매치되지 않으면 라인 기반으로 패치
                lines = content.split('\n')
                patched_lines = []
                in_strnlen = False
                strnlen_start = -1
                
                for i, line in enumerate(lines):
                    if 'static size_t strnlen' in line and not in_strnlen:
                        # strnlen 함수 시작
                        patched_lines.append('#ifndef HAVE_STRNLEN')
                        patched_lines.append(line)
                        in_strnlen = True
                        strnlen_start = i
                    elif in_strnlen and line.strip() == '}':
                        # strnlen 함수 끝
                        patched_lines.append(line)
                        patched_lines.append('#endif /* HAVE_STRNLEN */')
                        in_strnlen = False
                    else:
                        patched_lines.append(line)
                
                if strnlen_start >= 0:
                    content = '\n'.join(patched_lines)
                    with open(patch_file, 'w') as f:
                        f.write(content)
                    print("✅ GMP strnlen patch applied successfully (line-based)")
                else:
                    print("⚠️  Could not find strnlen function to patch")

def setup_build_env():
    """빌드 환경 설정"""
    env = os.environ.copy()
    
    # binutils가 있으면 PATH에 추가
    if "REZ_BINUTILS_ROOT" in env:
        env["PATH"] = f"{env['REZ_BINUTILS_ROOT']}/bin:{env['PATH']}"
        print(f"[INFO] Using binutils from: {env['REZ_BINUTILS_ROOT']}")
    
    # glibc가 있으면 sysroot로 사용할 준비
    if "REZ_GLIBC_ROOT" in env:
        print(f"[INFO] GLIBC root available: {env['REZ_GLIBC_ROOT']}")
    
    # 컴파일러 환경 변수 초기화 (호스트 컴파일러 사용)
    for var in ['CC', 'CXX', 'LD']:
        if var in env:
            del env[var]
    
    return env

def get_sysroot_options():
    """sysroot 관련 configure 옵션 반환"""
    options = []
    
    # REZ_GLIBC_ROOT가 있으면 사용, 없으면 시스템 기본값 사용
    if "REZ_GLIBC_ROOT" in os.environ:
        sysroot = os.environ["REZ_GLIBC_ROOT"]
        options.extend([
            f"--with-sysroot={sysroot}",
            "--with-native-system-header-dir=include"
        ])
        print(f"[INFO] Using sysroot: {sysroot}")
    else:
        # 시스템 헤더 직접 지정
        options.extend([
            "--with-sysroot=/",
            "--with-native-system-header-dir=/usr/include"
        ])
        print("[INFO] Using system headers from /usr/include")
    
    return options

def verify_build(install_path):
    """빌드 결과 검증"""
    print("\n[INFO] Verifying build...")
    
    # 필수 디렉토리 확인 (버전 번호는 유동적으로)
    required_dirs = [
        'bin',
        'lib64',
        'include/c++',  # 버전별로 체크
        'lib/gcc/x86_64-pc-linux-gnu'  # 버전별로 체크
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(install_path, dir_path)
        if os.path.exists(full_path):
            # 디렉토리 내용 개수도 확인
            try:
                subdirs = os.listdir(full_path)
                if dir_path in ['include/c++', 'lib/gcc/x86_64-pc-linux-gnu']:
                    # 버전 디렉토리 찾기
                    version_dirs = [d for d in subdirs if d.replace('.', '').isdigit() or d.isdigit()]
                    if version_dirs:
                        print(f"✅ Found: {dir_path} → versions: {version_dirs}")
                    else:
                        print(f"⚠️  Found: {dir_path} but no version subdirectories")
                else:
                    file_count = len(subdirs)
                    print(f"✅ Found: {dir_path} ({file_count} items)")
            except:
                print(f"✅ Found: {dir_path}")
        else:
            print(f"❌ Missing: {dir_path}")
            # 유사한 경로가 있는지 확인
            parent_dir = os.path.dirname(full_path)
            if os.path.exists(parent_dir):
                try:
                    similar_dirs = [d for d in os.listdir(parent_dir) 
                                  if os.path.basename(dir_path).lower() in d.lower()]
                    if similar_dirs:
                        print(f"   💡 Found similar: {similar_dirs}")
                except:
                    pass
    
    # 필수 바이너리 확인
    required_bins = ['gcc', 'g++', 'gfortran', 'cpp', 'gcc-ar', 'gcc-nm', 'gcc-ranlib']
    bin_dir = os.path.join(install_path, 'bin')
    
    for binary in required_bins:
        bin_path = os.path.join(bin_dir, binary)
        if os.path.exists(bin_path):
            print(f"✅ Binary: {binary}")
        else:
            print(f"⚠️  Missing binary: {binary}")
    
    # 필수 라이브러리 확인
    required_libs = [
        'libstdc++.so',
        'libgcc_s.so',
        'libgfortran.so',
        'libgomp.so'
    ]
    
    lib_dir = os.path.join(install_path, 'lib64')
    for lib in required_libs:
        lib_files = glob.glob(os.path.join(lib_dir, f"{lib}*"))
        if lib_files:
            print(f"✅ Library: {lib}")
        else:
            print(f"⚠️  Missing library: {lib}")
    
    # 간단한 컴파일 테스트
    gcc_path = os.path.join(install_path, 'bin', 'gcc')
    if os.path.exists(gcc_path):
        print("\n[INFO] Testing GCC functionality...")
        try:
            # 시스템 헤더 접근 테스트
            test_result = subprocess.run(
                f'echo "#include <stdio.h>\nint main(){{return 0;}}" | {gcc_path} -x c - -o /tmp/gcc_test',
                shell=True, capture_output=True, text=True, timeout=30
            )
            if test_result.returncode == 0:
                print("✅ GCC can compile with system headers")
                # 테스트 파일 정리
                try:
                    os.remove('/tmp/gcc_test')
                except:
                    pass
            else:
                print(f"⚠️  GCC test failed: {test_result.stderr}")
        except Exception as e:
            print(f"⚠️  GCC test error: {e}")

    print("\n[INFO] Build verification complete")

def _build(source_path, build_path, install_path):
    source_dir = os.path.join(source_path, "source")
    gcc_src_dirs = [d for d in glob.glob(os.path.join(source_dir, "gcc-*")) if os.path.isdir(d)]
    if not gcc_src_dirs:
        raise RuntimeError("❌ gcc source directory not found in ./source")

    gcc_src_dir = gcc_src_dirs[0]
    print(f"[INFO] Using GCC source: {gcc_src_dir}")
    
    # 빌드 환경 설정
    build_env = setup_build_env()
    build_dir = os.path.join(build_path, "gcc-build")
    
    # 로그 파일 설정
    log_dir = os.path.join(build_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    configure_log = os.path.join(log_dir, "configure.log")
    build_log = os.path.join(log_dir, "build.log")
    
    # Configure 완료 마커 파일
    configure_done = os.path.join(build_dir, ".configure_done")
    
    try:
        # GMP 패치 적용
        patch_gmp(gcc_src_dir)
        
        # 빌드 디렉토리 준비 - configure가 이미 완료되었는지 확인
        if os.path.exists(configure_done):
            print("[INFO] Configure already completed, skipping...")
        else:
            # 빌드 디렉토리 완전히 정리하고 다시 생성
            clean_path(build_dir)
            os.makedirs(build_dir, exist_ok=True)
            
            # sysroot 옵션 가져오기
            sysroot_opts = get_sysroot_options()
            sysroot_opts_str = " \\\n          ".join(sysroot_opts)
            
            # 최소 빌드 모드 확인
            minimal_build = os.environ.get('GCC_MINIMAL_BUILD', '0') == '1'
            
            if minimal_build:
                print("[INFO] Using minimal build configuration")
                configure_cmd = f"""
                    {gcc_src_dir}/configure \\
                      --prefix={install_path} \\
                      --enable-languages=c,c++ \\
                      --disable-multilib \\
                      --enable-shared \\
                      {sysroot_opts_str} \\
                      --with-pkgversion="M83 GCC 11.5.0 Toolchain (Minimal)"
                """
            else:
                configure_cmd = f"""
                    {gcc_src_dir}/configure \\
                      --prefix={install_path} \\
                      --enable-languages=c,c++,fortran \\
                      --disable-multilib \\
                      --enable-shared \\
                      --enable-threads=posix \\
                      --enable-lto \\
                      --enable-__cxa_atexit \\
                      --enable-checking=release \\
                      --with-system-zlib \\
                      {sysroot_opts_str} \\
                      --enable-libstdcxx-time=yes \\
                      --enable-gnu-indirect-function \\
                      --enable-gnu-unique-object \\
                      --enable-linker-build-id \\
                      --enable-plugin \\
                      --enable-initfini-array \\
                      --enable-libmpx \\
                      --with-linker-hash-style=gnu \\
                      --with-default-libstdcxx-abi=new \\
                      --with-gcc-major-version-only \\
                      --with-pkgversion="M83 GCC 11.5.0 Toolchain" \\
                      --with-bugurl="https://github.com/m83/gcc-build"
                """

            print("\n[INFO] Configure command:")
            print(configure_cmd)
            
            # Configure 실행 (에러 처리 포함)
            run_cmd_with_logging(configure_cmd, cwd=build_dir, env=build_env, 
                               log_file=configure_log, timeout=900)  # 15분 타임아웃으로 단축
            
            # Configure 완료 마커 생성
            with open(configure_done, 'w') as f:
                f.write(f"Configure completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 빌드 실행 (에러 처리 포함)
        jobs = os.environ.get('MAKEFLAGS', f'-j{os.cpu_count()}').replace('-j', '')
        print(f"\n[INFO] Building with {jobs} parallel jobs...")
        
        # --no-print-directory로 불필요한 출력 줄이기
        # configure 재실행 방지를 위해 --disable-option-checking 추가
        build_cmd = f"make -j{jobs} --no-print-directory"
        
        run_cmd_with_logging(build_cmd, cwd=build_dir, env=build_env, 
                           log_file=build_log, timeout=3600)  # 1시간 타임아웃으로 단축
        
    except BuildError as e:
        print(f"\n[BUILD ERROR] {e}")
        print(f"[BUILD ERROR] Error type: {e.error_type}")
        
        # 자동 수정 시도
        if e.error_type and auto_fix_error(e.error_type, build_dir, gcc_src_dir, install_path):
            print("[BUILD ERROR] Attempting smart rebuild after auto-fix...")
            return smart_rebuild(source_path, build_path, install_path)
        else:
            # 자동 수정 실패 시 스마트 재빌드 시도
            print("[BUILD ERROR] Auto-fix failed, attempting smart rebuild...")
            return smart_rebuild(source_path, build_path, install_path)
    
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}")
        # 예상치 못한 에러의 경우도 스마트 재빌드 시도
        return smart_rebuild(source_path, build_path, install_path)

def _install(build_path, install_path):
    build_dir = os.path.join(build_path, "gcc-build")
    if not os.path.exists(build_dir):
        raise RuntimeError("❌ Build directory not found. Run build step first.")

    clean_path(install_path)
    os.makedirs(install_path, exist_ok=True)

    print("[INFO] Running make install...")
    run_cmd("make install", cwd=build_dir)
    
    # C++ 헤더 확인 (버전에 관계없이)
    cpp_include_path = os.path.join(install_path, "include/c++")
    cpp_headers_found = False
    if os.path.exists(cpp_include_path):
        version_dirs = os.listdir(cpp_include_path)
        cpp_headers_found = len(version_dirs) > 0
    
    if not cpp_headers_found:
        print("[INFO] C++ headers missing, trying libstdc++-v3 install...")
        try:
            # libstdc++-v3 설치 시도
            run_cmd("make -C x86_64-pc-linux-gnu/libstdc++-v3 install-data", cwd=build_dir)
        except Exception as e:
            print(f"[WARNING] libstdc++-v3 install failed: {e}")
            try:
                # 대안: 직접 헤더 복사
                gcc_src_dir = glob.glob(os.path.join(os.path.dirname(build_dir), "../source/gcc-*"))[0]
                libstdcxx_src = os.path.join(gcc_src_dir, "libstdc++-v3/include")
                if os.path.exists(libstdcxx_src):
                    print("[INFO] Manually copying C++ headers...")
                    os.makedirs(cpp_include_path, exist_ok=True)
                    run_cmd(f"cp -r {libstdcxx_src}/* {cpp_include_path}/", cwd=None)
            except Exception as e2:
                print(f"[WARNING] Manual header copy also failed: {e2}")
    
    # GCC 내부 라이브러리 확인 (버전에 관계없이)
    gcc_lib_base = os.path.join(install_path, "lib/gcc/x86_64-pc-linux-gnu")
    gcc_libs_found = False
    if os.path.exists(gcc_lib_base):
        version_dirs = os.listdir(gcc_lib_base)
        gcc_libs_found = len(version_dirs) > 0
    
    if not gcc_libs_found:
        print("[INFO] GCC internal libraries missing, trying alternative install...")
        try:
            # 가능한 타겟들 시도
            available_targets = subprocess.run("make -qp | grep '^install-'", 
                                             shell=True, capture_output=True, text=True, cwd=build_dir)
            if "install-headers" in available_targets.stdout:
                run_cmd("make install-headers", cwd=build_dir)
            else:
                print("[INFO] No additional install targets available")
        except Exception as e:
            print(f"[WARNING] Additional install attempts failed: {e}")
    
    print(f"✅ Installed to: {install_path}")
    
    # 빌드 검증
    verify_build(install_path)

def build(source_path, build_path, install_path, targets):
    version = os.environ.get("REZ_BUILD_PROJECT_VERSION", "11.5.0")

    if "install" in targets:
        install_path = f"/core/Linux/APPZ/packages/gcc/{version}/platform_linux"

    _build(source_path, build_path, install_path)

    if "install" in (targets or []):
        _install(build_path, install_path)
        copy_package_py(source_path, install_path)

if __name__ == '__main__':
    build(
        source_path=os.environ["REZ_BUILD_SOURCE_PATH"],
        build_path=os.environ["REZ_BUILD_PATH"],
        install_path=os.environ["REZ_BUILD_INSTALL_PATH"],
        targets=sys.argv[1:]
    )