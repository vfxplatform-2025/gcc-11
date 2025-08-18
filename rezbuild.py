# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import glob
import shutil

def run_cmd(cmd, cwd=None, env=None):
    print(f"[RUN] {cmd}")
    subprocess.run(cmd, cwd=cwd, env=env or os.environ, shell=True, check=True)

def clean_path(path):
    if os.path.exists(path):
        print(f"🧹 Removing: {path}")
        shutil.rmtree(path)

def copy_package_py(source_path, install_path):
    src = os.path.join(source_path, "package.py")
    dst = os.path.join(install_path, "package.py")
    if os.path.exists(src):
        print(f"📄 Copying package.py → {dst}")
        shutil.copy(src, dst)

def _build(source_path, build_path, install_path):
    source_dir = os.path.join(source_path, "source")
    gcc_src_dirs = [d for d in glob.glob(os.path.join(source_dir, "gcc-*")) if os.path.isdir(d)]
    if not gcc_src_dirs:
        raise RuntimeError("❌ gcc source directory not found in ./source")

    gcc_src_dir = gcc_src_dirs[0]
    print(f"[INFO] Using GCC source: {gcc_src_dir}")

    build_dir = os.path.join(build_path, "gcc-build")
    clean_path(build_dir)
    os.makedirs(build_dir, exist_ok=True)

    configure_cmd = f"""
        {gcc_src_dir}/configure \
          --prefix={install_path} \
          --enable-languages=c,c++,fortran \
          --disable-multilib \
          --enable-shared \
          --enable-threads=posix \
          --enable-lto \
          --enable-__cxa_atexit \
          --enable-checking=release \
          --with-system-zlib \
          --with-pkgversion="M83 GCC 11.5.0 Toolchain"
    """  # 삭제: --with-glibc-version / --with-native-system-header-dir

    run_cmd(configure_cmd, cwd=build_dir)
    run_cmd("make -j$(nproc)", cwd=build_dir)

def _install(build_path, install_path):
    build_dir = os.path.join(build_path, "gcc-build")
    if not os.path.exists(build_dir):
        raise RuntimeError("❌ Build directory not found. Run build step first.")

    clean_path(install_path)
    os.makedirs(install_path, exist_ok=True)

    print("[INFO] Running make install...")
    run_cmd("make install", cwd=build_dir)
    print(f"✅ Installed to: {install_path}")

def build(source_path, build_path, install_path, targets):
    version = os.environ.get("REZ_BUILD_PROJECT_VERSION", "11.5.0")

    if "install" in targets:
        install_path = f"/core/Linux/APPZ/packages/gcc/{version}"

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

