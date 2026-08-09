# build_winpython.py
import os, sys, argparse, datetime, subprocess, shutil
import logging

from pathlib import Path
from filecmp import cmp

def setup_logging(log_file: Path, LOG_FORMAT="%(asctime)s %(levelname)s: %(message)s"):
    """Initialize logging to both file and stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding="utf-8", mode='a')
        ]
    )

def log_section(message: str, highlight_bar="-"*40):
    logging.info("\n" + highlight_bar)
    logging.info(message)
    logging.info(highlight_bar)

def delete_folder_if_exists(folder: Path, check_flavor: str = ""):
    check_last = folder.parent.name if not folder.is_dir() else folder.name
    expected_name = "bu" + check_flavor
    if folder.exists() and folder.is_dir() and check_last == expected_name:
        logging.info(f"Removing old backup: {folder}")
        folder_old = folder.with_suffix('.old')
        if folder_old.exists():
            shutil.rmtree(folder_old)
        folder.rename(folder_old)
        shutil.rmtree(folder_old)

def run_command(cmd, shell=False, check=True):
    logging.info(f"[RUNNING] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    with subprocess.Popen(
        cmd, shell=shell, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True
    ) as proc:
        for line in proc.stdout:
            logging.info(line.rstrip())
    if check and proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)

def pip_install(python_exe: Path, req_file: str, constraints: str, find_links: str, label: str, options:[]):
    if req_file and Path(req_file).exists():
        cmd = [
            str(python_exe), "-m", "pip", "install",
            "-r", req_file, "-c", constraints,
            "--pre", "--no-index", f"--find-links={find_links}",
            "--upgrade", "--no-warn-script-location"
        ]
        if options:
            cmd += options
        log_section(f"Pip-install {label}")
        run_command(cmd)
    else:
        log_section(f"No {label} specified/skipped")

def parse_bytecode_mode(value: str):
    """Interpret --bytecode. Returns (skip pip's inline compile, compileall jobs).

    pip        pip byte-compiles inline as it always has (default, unchanged)
    none       no .pyc at all -- for throwaway builds: pylock, size pre-check
    parallel   pip --no-compile, then one compileall pass over every core
    parallel-N same, capped at N workers
    """
    mode = (value or "pip").strip().lower()
    if mode == "pip":
        return False, None
    if mode == "none":
        return True, None
    if mode == "parallel":
        return True, 0  # compileall -j0 = one worker per core
    if mode.startswith("parallel-") and mode[9:].isdigit():
        return True, int(mode[9:])
    raise ValueError(f"--bytecode must be pip, none, parallel or parallel-N (got {value!r})")


def compile_bytecode(target_python: Path, jobs: int):
    """Byte-compile site-packages in one pass, using the *target* interpreter.

    pip compiles serially while installing; doing it afterwards lets it run
    across cores. Failures stay non-fatal: some packages ship modules that are
    not importable on this Python, and pip tolerates those too.
    """
    site_packages = target_python.parent / "Lib" / "site-packages"
    log_section(f"Byte-compiling {site_packages} (-j{jobs})")
    run_command([str(target_python), "-m", "compileall", "-q", f"-j{jobs}", str(site_packages)], check=False)


def patch_winpython(python_exe):
    cmd = [
        str(python_exe), "-c",
        "from wppm import wppm; wppm.Distribution().patch_standard_packages('', to_movable=True)"
    ]
    run_command(cmd)

def check_env_bat(winpydirbase: Path):
    envbat = winpydirbase / "scripts" / "env.bat"
    if not envbat.exists():
        raise FileNotFoundError(f"Missing env.bat at {envbat}")

def generate_lockfiles(target_python: Path, winpydirbase: Path, constraints: str, find_links: str, file_postfix: str):
    pip_req = winpydirbase.parent / "requirement_temp.txt"
    with subprocess.Popen([str(target_python), "-m", "pip", "freeze"], stdout=subprocess.PIPE) as proc:
        packages = [l for l in proc.stdout if b"winpython" not in l]
    pip_req.write_bytes(b"".join(packages))
    # Lock to web and local (scaffolding)
    for kind in ("", "local"):
        out = winpydirbase.parent / f"pylock.{file_postfix}{kind}.toml"
        outreq = winpydirbase.parent / f"requir.{file_postfix}{kind}.txt"
        cmd = [str(target_python), "-m", "pip", "lock", "--no-deps", "-c", constraints]
        if kind == "local":
            cmd += ["--find-links", find_links]
        cmd += ["-r", str(pip_req), "-o", str(out)]
        run_command(cmd)
    # Convert both locks to requirement.txt with hash256
        cmd = [str(target_python), "-X", "utf8", "-c", f"from wppm import wheelhouse as wh; wh.pylock_to_req(r'{out}', r'{outreq}')"]
        run_command(cmd)
    # check equality
    web, local = "", "local"
    if not cmp(winpydirbase.parent / f"requir.{file_postfix}{web}.txt", winpydirbase.parent / f"requir.{file_postfix}{local}.txt"):
        print("⚠️⚠️⚠️⚠️⚠️⚠️ ALARM ⚠️⚠️⚠️⚠️⚠️⚠️differences in ", winpydirbase.parent / f"requir.{file_postfix}{web}.txt", winpydirbase.parent / f"requir.{file_postfix}{local}.txt")
        raise os.error
    else:
        print ("💖💖💖 match 💖💖💖 ok ",winpydirbase.parent / f"requir.{file_postfix}{web}.txt", winpydirbase.parent / f"requir.{file_postfix}{local}.txt")
        print ("💖 housekeeping, removing local files 💖 ",  winpydirbase.parent / f"requir.{file_postfix}{local}.txt")
        os.remove (winpydirbase.parent / f"requir.{file_postfix}{local}.txt")
        os.remove (winpydirbase.parent / f"pylock.{file_postfix}{local}.toml")
        os.remove (winpydirbase.parent / f"requirement_temp.txt")
        if (winpydirbase.parent / f"requir.{file_postfix}_wheelslocal.txt").is_file():
            os.remove (winpydirbase.parent / f"requir.{file_postfix}_wheelslocal.txt")
        if (winpydirbase.parent / f"pylock.{file_postfix}_wheelslocal.toml").is_file():
            os.remove (winpydirbase.parent / f"pylock.{file_postfix}_wheelslocal.toml")

# --- Main Logic ---
def run_make_py(build_python, winpydirbase, args, winpyver, winpyver2):
    from . import make
    make.make_all(
        args.release, args.release_level, basedir_wpy=winpydirbase,
        verbose=True, flavor=args.flavor,
        source_dirs=args.source_dirs, toolsdirs=args.tools_dirs,
        winpyver=winpyver, winpyver2=winpyver2
    )

def process_wheelhouse_requirements(target_python: Path, winpydirbase: Path,args: argparse.Namespace,file_postfix: str):
    """
    Handle installation and conversion of wheelhouse requirements.
    """
    wheelhousereq = Path(args.wheelhousereq)
    kind = "local"
    out = winpydirbase.parent / f"pylock.{file_postfix}_wheels{kind}.toml"
    outreq = winpydirbase.parent / f"requir.{file_postfix}_wheels{kind}.txt"
    if wheelhousereq.is_file():
        # Generate pylock from wheelhousereq
        cmd = [
            str(target_python), "-m", "pip", "lock", "--no-index", "--trusted-host=None", "--pre", 
            "--find-links", args.find_links, "-c", args.constraints, "-r", str(wheelhousereq),
            "-o", str(out)
        ]
        run_command(cmd)
        # Convert pylock to requirements with hash
        pylock_to_req_cmd = [
            str(target_python), "-X", "utf8", "-c",
            f"from wppm import wheelhouse as wh; wh.pylock_to_req(r'{out}', r'{outreq}')"
        ]
        run_command(pylock_to_req_cmd, check=False)

        kind = ""
        outw = winpydirbase.parent / f"pylock.{file_postfix}_wheels{kind}.toml"
        outreqw = winpydirbase.parent / f"requir.{file_postfix}_wheels{kind}.txt"
        # Generate web pylock from local frozen hashes
        web_lock_cmd = [
            str(target_python), "-m", "pip", "lock", "--no-deps", "--require-hashes",
            "-r", str(outreq), "-o", str(outw)
        ]
        run_command(web_lock_cmd)
        pylock_to_req_cmd2 = [
            str(target_python), "-X", "utf8", "-c",
            f"from wppm import wheelhouse as wh; wh.pylock_to_req(r'{outw}', r'{outreqw}')"
        ]
        run_command(pylock_to_req_cmd2, check=False)

        # Use wppm to download local from req made with web hashes
        wheelhouse = winpydirbase / "wheelhouse" / "included.wheels"
        wppm_cmd = [
            str(target_python), "-X", "utf8", "-m", "wppm", str(out), "-ws", args.find_links,
            "-wd", str(wheelhouse)
        ]
        run_command(wppm_cmd, check=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python-target', required=True, help='Target Python version, e.g. 311')
    parser.add_argument('--release', default='', help='Release')
    parser.add_argument('--flavor', default='', help='Build flavor')
    parser.add_argument('--arch', default='64', help='Architecture')
    parser.add_argument('--release-level', default='', help='Release level (e.g., b1, b2)')
    parser.add_argument('--winpydirbase', required=True, help='Path to put environment')
    parser.add_argument('--source_dirs', required=True, help='Path to directory with python zip')
    parser.add_argument('--tools_dirs', required=True, help='Path to directory with python zip')
    parser.add_argument('--buildenv', required=True, help='Path to build environment')
    parser.add_argument('--constraints', default='constraints.txt', help='Constraints file')
    parser.add_argument('--requirements', help='Main requirements.txt file')
    parser.add_argument('--find-links', default='wheelhouse', help='Path to local wheelhouse')
    parser.add_argument('--log-dir', default='WinPython_build_logs', help='Directory for logs')
    parser.add_argument('--mandatory-req', help='Mandatory requirements file')
    parser.add_argument('--wheelhousereq', help='Wheelhouse requirements file')
    parser.add_argument('--bytecode', default='pip',
                        help="byte-compilation: 'pip' (inline, the default and what ships), "
                             "'none' (no .pyc -- for throwaway builds such as pylock generation "
                             "or a size pre-check), 'parallel' or 'parallel-N' (pip --no-compile, "
                             "then one compileall pass over N cores)")
    parser.add_argument('--create-installer', default='', help='default installer to create')
    args = parser.parse_args()

    # compute paths (same as Step2)...
    build_python = Path(args.buildenv) / "python.exe"
    winpydirbase = Path(args.winpydirbase)
    target_python = winpydirbase / "python" / "python.exe"

    # Setup paths and logs
    now = datetime.datetime.now()
    log_dir = Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)
    time_str = now.strftime("%Y-%m-%d_at_%H%M")
    log_file = log_dir / f"build_{args.python_target}_{args.flavor}_{args.release_level}_{time_str}.txt"
    setup_logging(log_file)

    # Logs termination and version naming
    if len(args.release_level) > 0:
        z = Path(winpydirbase).name[(4+len(args.arch)):-len(args.release_level)-len(args.release)]
    else:
        z = Path(winpydirbase).name[(4+len(args.arch)):-len(args.release)]
    tada = f"{z[:1]}_{z[1:3]}_{z[3:]}_{args.release}"
    winpyver2 = tada.replace('_', '.')
    winpyver = f"{winpyver2}{args.flavor}{args.release_level}"
    file_postfix = f"{args.arch}-{tada}{args.flavor}{args.release_level}"

    log_section(f"Preparing build for Python {args.python_target} ({args.arch}-bit)")

    log_section(f"🙏 Step 1: displace old {Path(winpydirbase)}")
    delete_folder_if_exists(winpydirbase.parent, check_flavor=args.flavor) #bu{flavor]}

    log_section(f"🙏 Step 2: make.py Python with {str(build_python)} at ({winpydirbase}")
    run_make_py(str(build_python), winpydirbase, args, winpyver, winpyver2)

    check_env_bat(winpydirbase)

    log_section("🙏 Step 3: install requirements")

    no_compile, compile_jobs = parse_bytecode_mode(args.bytecode)
    pip_options = ["--force-reinstall"] + (["--no-compile"] if no_compile else [])
    for label, req in [
        ("Mandatory", args.mandatory_req),
        ("Main", args.requirements),
    ]:
        pip_install(target_python, req, args.constraints, args.find_links, label, pip_options)

    log_section("🙏 Step 4: Patch Winpython")
    patch_winpython(target_python)

    # after patching, so the patched sources are the ones compiled
    if compile_jobs is not None:
        log_section("🙏 Step 4b: byte-compile")
        compile_bytecode(target_python, compile_jobs)
    elif no_compile:
        log_section("🙏 Step 4b: byte-compile skipped (--bytecode none)")

    log_section(f"🙏 Step 5: install wheelhouse requirements {args.wheelhousereq}")
    if args.wheelhousereq:
        process_wheelhouse_requirements(target_python, winpydirbase, args, file_postfix)

    log_section("🙏 Step 6: install lockfiles")
    print(target_python, winpydirbase, args.constraints, args.find_links, file_postfix)
    generate_lockfiles(target_python, winpydirbase, args.constraints, args.find_links, file_postfix)


    log_section(f"🙏 Step 7: generate changelog") 
    mdn = f"WinPython{args.flavor}-{args.arch}bit-{winpyver2}.md"
    out = f"WinPython{args.flavor}-{args.arch}bit-{winpyver2}_History.md"
    changelog_dir = log_dir.parent/ "changelogs"
    
    cmd = ["set", f"WINPYVER2={winpyver2}&",  "set",  f"WINPYFLAVOR={args.flavor}&",
        "set", f"WINPYVER={winpyver2}{args.flavor}{args.release_level}&",
        str(target_python), "-X", "utf8", "-c" , 
        (
        "from wppm import wppm;"
        "result = wppm.Distribution().generate_package_index_markdown();"
        f"open(r'{winpydirbase.parent / mdn}', 'w', encoding='utf-8').write(result)"
        )]
    run_command(cmd, shell=True)
    shutil.copyfile (winpydirbase.parent / mdn, changelog_dir / mdn)
    
    cmd = [str(target_python), "-X", "utf8", "-c",
        (
        "from wppm import diff;"
        f"result = diff.compare_package_indexes('{winpyver2}', searchdir=r'{changelog_dir}', flavor=r'{args.flavor}', architecture={args.arch});"
        f"open(r'{winpydirbase.parent / out}', 'w', encoding='utf-8').write(result)" 
        )]
    run_command(cmd, check=False)
    shutil.copyfile (winpydirbase.parent / out, changelog_dir / out)

    if args.create_installer != "":
        log_section("🙏 Step 8: Create Installer")
        stem = f"WinPython{args.arch}-{winpyver2}{args.flavor}{args.release_level}"
        cmd = [str(target_python), "-c",
        f"from wppm import utils; utils.command_installer_7zip(r'{winpydirbase}', r'{winpydirbase.parent}', r'{stem}', r'{args.create_installer}')" ]
        run_command(cmd, check=False)

if __name__ == '__main__':
    main()
