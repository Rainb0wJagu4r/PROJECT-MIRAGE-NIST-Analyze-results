"""
Build script to compile PractRand, TestU01, and NIST STS binaries from source.
Works on Windows (MinGW/Clang/GCC) and Linux/macOS.
"""
import os
import sys
import subprocess
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
SCRATCH_DIR = os.path.join(ROOT_DIR, "build_tmp")

def build_practrand():
    print("[+] Building PractRand 0.94...")
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    practrand_src = os.path.join(SCRATCH_DIR, "PractRand")
    if not os.path.exists(practrand_src):
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/MartyMacGyver/PractRand.git", practrand_src], check=True)
    
    out_exe = os.path.join(TOOLS_DIR, "RNG_test.exe" if sys.platform == "win32" else "RNG_test")
    cmd = f"g++ -O3 -Iinclude -Isrc src/*.cpp src/RNGs/*.cpp src/RNGs/other/*.cpp tools/RNG_test.cpp -o \"{out_exe}\""
    subprocess.run(cmd, shell=True, cwd=practrand_src, check=True)
    print(f"    PractRand compiled successfully: {out_exe}")

def build_testu01():
    print("[+] Building TestU01 1.2.3...")
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    tu01_src = os.path.join(SCRATCH_DIR, "TestU01")
    if not os.path.exists(tu01_src):
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/blep/TestU01.git", tu01_src], check=True)
    
    # Generate headers using tcode
    tcode_exe = os.path.join(tu01_src, "tcode.exe" if sys.platform == "win32" else "tcode")
    subprocess.run(["gcc", os.path.join(tu01_src, "mylib", "tcode.c"), "-o", tcode_exe], check=True)
    
    inc_dir = os.path.join(tu01_src, "include")
    os.makedirs(inc_dir, exist_ok=True)
    import glob
    for folder in ['mylib', 'probdist', 'testu01']:
        fdir = os.path.join(tu01_src, folder)
        for tex in glob.glob(os.path.join(fdir, '*.tex')):
            b = os.path.splitext(os.path.basename(tex))[0]
            if b.startswith('guide') or b.startswith('annexe') or b == 'titre':
                continue
            subprocess.run([tcode_exe, tex, os.path.join(inc_dir, b + '.h')])
            subprocess.run([tcode_exe, tex, os.path.join(fdir, b + '.h')])
            
    with open(os.path.join(inc_dir, 'gdefconf.h'), 'w') as f:
        f.write("#ifndef GDEFCONF_H\n#define GDEFCONF_H\n#define HAVE_LONG_LONG 1\n#define HAVE_ERF 1\n#define HAVE_LGAMMA 1\n#define HAVE_STDINT_H 1\n#define USE_ANSI_CLOCK 1\n#endif\n")
    with open(os.path.join(inc_dir, 'config.h'), 'w') as f:
        f.write("#ifndef CONFIG_H\n#define CONFIG_H\n#define HAVE_LONG_LONG 1\n#define HAVE_ERF 1\n#define HAVE_LGAMMA 1\n#define HAVE_STDINT_H 1\n#define HAVE_WINDOWS_H 1\n#define PACKAGE_STRING \"TestU01 1.2.3\"\n#define USE_ANSI_CLOCK 1\n#endif\n")

    # Compile objects
    objs = []
    for folder in ['mylib', 'probdist', 'testu01']:
        fdir = os.path.join(tu01_src, folder)
        for c in glob.glob(os.path.join(fdir, '*.c')):
            b = os.path.basename(c)
            if b in ['tcode.c', 'ucryptoIS.c']:
                continue
            obj = os.path.splitext(c)[0] + '.o'
            subprocess.run(['gcc', '-O2', '-w', '-DHAVE_CONFIG_H', '-DHAVE_WINDOWS_H', '-I' + inc_dir, '-I' + os.path.join(tu01_src, 'mylib'), '-I' + os.path.join(tu01_src, 'probdist'), '-I' + os.path.join(tu01_src, 'testu01'), '-c', c, '-o', obj], check=True)
            objs.append(obj)
            
    lib_path = os.path.join(tu01_src, "libtestu01.a")
    subprocess.run(["ar", "rcs", lib_path] + objs, check=True)
    
    # Compile runner
    runner_c = os.path.join(ROOT_DIR, "testu01_runner.c")
    runner_exe = os.path.join(TOOLS_DIR, "testu01_runner.exe" if sys.platform == "win32" else "testu01_runner")
    if os.path.exists(runner_c):
        subprocess.run(["gcc", "-O2", "-I" + inc_dir, runner_c, lib_path, "-o", runner_exe, "-lm"], check=True)
        print(f"    TestU01 runner compiled successfully: {runner_exe}")

if __name__ == "__main__":
    os.makedirs(TOOLS_DIR, exist_ok=True)
    try:
        build_practrand()
    except Exception as e:
        print(f"Error building PractRand: {e}")
    try:
        build_testu01()
    except Exception as e:
        print(f"Error building TestU01: {e}")
