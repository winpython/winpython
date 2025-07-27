# build_winpython.py
import os, sys, argparse, datetime, subprocess, shutil
from pathlib import Path

# --- Logging ---
def log_section(logfile, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    section = f"\n{'-'*40}\n({ts}) {message}\n{'-'*40}\n"
    print(section)
    with open(logfile, 'a', encoding='utf-8') as f:
        f.write(section)


# --- Utility Functions ---

def delete_folder_if_exists(folder: Path, check_flavor: str = ""):
    check_last = folder.parent.name if not folder.is_dir() else folder.name
    expected_name = "bu" + check_flavor

    if folder.exists() and folder.is_dir() and check_last == expected_name:
        print("Removing old backup:", folder)
        folder_old = folder.with_suffix('.old')
        if folder_old.exists():
            shutil.rmtree(folder_old)
        folder.rename(folder_old)
        shutil.rmtree(folder_old)


def run_command(cmd, log_file=None, shell=False, check=True):
    print(f"[RUNNING] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    with subprocess.Popen(
        cmd, shell=shell, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, universal_newlines=True
    ) as proc:
        with open(log_file, 'a', encoding='utf-8') if log_file else open(os.devnull, 'w') as logf:
            for line in proc.stdout:
                print(line, end="")
                logf.write(line)
    if check and proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def pip_install(python_exe: Path, req_file: str, constraints: str, find_links: str, logfile: Path, label: str):
    if req_file and Path(req_file).exists():
        cmd = [
            str(python_exe), "-m", "pip", "install",
            "-r", req_file, "-c", constraints,
            "--pre", "--no-index", f"--find-links={find_links}"
        ]
        log_section(logfile, f"Pip-install {label}")
        run_command(cmd, log_file=logfile)
    else:
        log_section(logfile, f"No {label} specified/skipped")


def patch_winpython(python_exe, logfile):
    cmd = [
        str(python_exe), "-c",
        "from wppm import wppm; wppm.Distribution().patch_standard_packages('', to_movable=True)"
    ]
    run_command(cmd, log_file=logfile)


def check_env_bat(winpydirbase: Path):
    envbat = winpydirbase / "scripts" / "env.bat"
    if not envbat.exists():
        raise FileNotFoundError(f"Missing env.bat at {envbat}")


def generate_lockfiles(target_python: Path, winpydirbase: Path, constraints: str, find_links: str, logfile: Path, file_postfix: str):
    pip_req = winpydirbase.parent / "requirement_temp.txt"
    with subprocess.Popen([str(target_python), "-m", "pip", "freeze"], stdout=subprocess.PIPE) as proc:
        packages = [l for l in proc.stdout if b"winpython" not in l]
    pip_req.write_bytes(b"".join(packages))
    # Lock to web and local (scaffolding)
    for kind in ("", "local"):
        out = winpydirbase.parent / f"pylock.{file_postfix}_{kind}.toml"
        outreq = winpydirbase.parent / f"requir.{file_postfix}_{kind}.txt"
        print(
            [str(target_python), "-m", "pip", "lock", "--no-deps", "-c", constraints] +
             (["--find-links",find_links] if kind =="local" else []) + 
             ["-r", str(pip_req), "-o", str(out)]
        )
        subprocess.run(
            [str(target_python), "-m", "pip", "lock", "--no-deps", "-c", constraints] +
             (["--find-links",find_links] if kind =="local" else []) + 
             ["-r", str(pip_req), "-o", str(out)],
            stdout=open(logfile, 'a'), stderr=subprocess.STDOUT, check=True
        )
    # Convert both locks to requirement.txt with hash256
        cmd = f"from wppm import wheelhouse as wh; wh.pylock_to_req(r'{out}', r'{outreq}')"
        print(
            [str(target_python), "-c", cmd]
        )
        subprocess.run(
            [str(target_python), "-c", cmd],
            stdout=open(logfile, 'a'), stderr=subprocess.STDOUT, check=False
        )
    # check equality
    from filecmp import cmp
    web, local = "", "local"
    if not cmp(winpydirbase.parent / f"requir.{file_postfix}_{web}.txt", winpydirbase.parent / f"requir.{file_postfix}_{local}.txt"):
       print("ALARM differences in ", winpydirbase.parent / f"requir.{file_postfix}_{web}.txt", winpydirbase.parent / f"requir.{file_postfix}_{local}.txt")
       raise os.error
    else:
       print ("match ok ",winpydirbase.parent / f"requir.{file_postfix}_{web}.txt", winpydirbase.parent / f"requir.{file_postfix}_{local}.txt")

# --- Main Logic ---
def run_make_py(build_python, winpydirbase, args, logfile):
    from . import make
    make.make_all(
        args.release, args.release_level, basedir_wpy=winpydirbase,
        verbose=True, flavor=args.flavor,
        source_dirs=args.source_dirs, toolsdirs=args.tools_dirs
    )
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python-target', required=True, help='Target Python version, e.g. 311')
    parser.add_argument('--release', default='', help='Release')
    parser.add_argument('--flavor', default='', help='Build flavor')
    parser.add_argument('--arch', default='64', help='Architecture')
    parser.add_argument('--release-level', default='b1', help='Release level (e.g., b1, rc)')
    parser.add_argument('--winpydirbase', required=True, help='Path to put environment')
    parser.add_argument('--source_dirs', required=True, help='Path to directory with python zip')
    parser.add_argument('--tools_dirs', required=True, help='Path to directory with python zip')
    parser.add_argument('--buildenv', required=True, help='Path to build environment')
    parser.add_argument('--constraints', default='constraints.txt', help='Constraints file')
    parser.add_argument('--requirements', help='Main requirements.txt file')
    parser.add_argument('--find-links', default='wheelhouse', help='Path to local wheelhouse')
    parser.add_argument('--log-dir', default='WinPython_build_logs', help='Directory for logs')
    parser.add_argument('--mandatory-req', help='Mandatory requirements file')
    parser.add_argument('--pre-req', help='Pre requirements file')
    parser.add_argument('--wheelhousereq', help='Wheelhouse requirements file')
    parser.add_argument('--create-installer', default='', help='default installer to create')
    args = parser.parse_args()

    # compute paths (same as Step2)...
    build_python = Path(args.buildenv) / "python.exe"
    winpydirbase = Path(args.winpydirbase)  # from Step2 logic
    target_python = winpydirbase / "python" / "python.exe"

    # Setup paths and logs
    now = datetime.datetime.now()
    log_dir = Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)
    time_str = now.strftime("%Y-%m-%d_at_%H%M")
    log_file = log_dir / f"build_{args.python_target}_{args.flavor}_{args.release_level}_{time_str}.txt"
    
    #logs termination
    z = Path(winpydirbase).name[(4+len(args.arch)):-len(args.release_level)]
    tada = f"{z[:1]}_{z[1:3]}_{z[3]}_{args.release}"
    winpyver2 = tada.replace('_', '.')
    file_postfix = f"{args.arch}-{tada}{args.flavor}{args.release_level}"

    log_section(log_file, f"Preparing build for Python {args.python_target} ({args.arch}-bit)")

    log_section(log_file, f"🙏 Step 0: displace old {Path(winpydirbase)}")

    delete_folder_if_exists(winpydirbase.parent, check_flavor=args.flavor) #bu{flavor]}

    log_section(log_file, f"🙏 Step 1: make.py Python with {str(build_python)} at ({winpydirbase}")
    run_make_py(str(build_python), winpydirbase, args, log_file)

    check_env_bat(winpydirbase)

    log_section(log_file, "🙏 Step 3: install requirements")

    for label, req in [
        ("Mandatory", args.mandatory_req),
        ("Pre", args.pre_req),
        ("Main", args.requirements),
    ]:
        pip_install(target_python, req, args.constraints, args.find_links, log_file, label)

    log_section(log_file, "🙏 Step 4: Patch Winpython")
    patch_winpython(target_python, log_file)

    if args.wheelhousereq:
        log_section(log_file, f"🙏 Step 5: install wheelhouse requirements {args.wheelhousereq}")
        wheelhousereq = Path(args.wheelhousereq)
        kind = "local"
        out = winpydirbase.parent / f"pylock.{file_postfix}_wheels{kind}.toml"
        outreq = winpydirbase.parent / f"requir.{file_postfix}_wheels{kind}.txt"
        if wheelhousereq.is_file():
            # Generate pylock from wheelhousereq
            cmd = [str(target_python), "-m" , "pip", "lock","--no-index", "--trusted-host=None",
            "--find-links", args.find_links, "-c", args.constraints, "-r", wheelhousereq,
            "-o", out ]
            subprocess.run(cmd, stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=True)    
            # Convert pylock to requirements with hash
            cmd = f"from wppm import wheelhouse as wh; wh.pylock_to_req(r'{out}', r'{outreq}')"
            print( [str(target_python), "-c", cmd] )
            subprocess.run([str(target_python), "-c", cmd],
                stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=False
            )

            kind = ""
            outw = winpydirbase.parent / f"pylock.{file_postfix}_wheels{kind}.toml"
            outreqw = winpydirbase.parent / f"requir.{file_postfix}_wheels{kind}.txt"
            # Generate web pylock from local frozen hashes
            cmd = [str(target_python), "-m" , "pip", "lock","--no-deps", "--require-hashes",
            "-r", str(outreq), "-o", str(outw) ]
            subprocess.run(cmd, stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=True)    
            cmd = f"from wppm import wheelhouse as wh; wh.pylock_to_req(r'{outw}', r'{outreqw}')"
            print( [str(target_python), "-c", cmd] )
            subprocess.run([str(target_python), "-c", cmd],
                stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=False
            )

            # Use wppm to download local from req made with web hashes
            wheelhouse = winpydirbase / "wheelhouse" / "included.wheels"
            cmd = [str(target_python), "-X", "utf8", "-m", "wppm", str(out), "-ws", args.find_links,
            "-wd", str(wheelhouse)
            ]
            print(cmd)
            subprocess.run(cmd, stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=False)


    log_section(log_file, "🙏 Step 6: install lockfiles")
    print(target_python, winpydirbase, args.constraints, args.find_links, log_file)
    generate_lockfiles(target_python, winpydirbase, args.constraints, args.find_links, log_file, file_postfix)

    # 6) generate changelog
    mdn = f"WinPython{args.flavor}-{args.arch}bit-{winpyver2}.md"
    out = f"WinPython{args.flavor}-{args.arch}bit-{winpyver2}_History.md"
    changelog_dir = log_dir.parent/ "changelogs"
    
    log_section(log_file, f"🙏 Step 6: generate changelog {mdn}") 

    cmd = ["set", f"WINPYVER2={winpyver2}&",  "set",  f"WINPYFLAVOR={args.flavor}&",
        "set", f"WINPYVER={winpyver2}{args.flavor}{args.release_level}&",
        str(target_python), "-c" , 
        (
        "from wppm import wppm;"
        "result = wppm.Distribution().generate_package_index_markdown();"
        f"open(r'{winpydirbase.parent / mdn}', 'w', encoding='utf-8').write(result)"
        )]
    print(cmd)
    subprocess.run(cmd, stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=True, shell=True)
    shutil.copyfile (winpydirbase.parent / mdn, changelog_dir / mdn)
    
    cmd = [str(target_python), "-c",
        (
        "from wppm import diff;"
        f"result = diff.compare_package_indexes('{winpyver2}', searchdir=r'{changelog_dir}', flavor=r'{args.flavor}', architecture={args.arch});"
        f"open(r'{winpydirbase.parent / out}', 'w', encoding='utf-8').write(result)" 
        )]
    subprocess.run(cmd, stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=True)
    shutil.copyfile (winpydirbase.parent / out, changelog_dir / out)
    log_section(log_file, "✅ Step 6 complete")

    if args.create_installer != "":
        log_section(log_file, "🙏 Step 7 Create Installer")
        stem = f"WinPython{args.arch}-{winpyver2}{args.flavor}{args.release_level}"
        cmd = f"from wppm import utils; utils.command_installer_7zip(r'{winpydirbase}', r'{winpydirbase.parent}', r'{stem}', r'{args.create_installer}')"
        print( [str(target_python), "-c", cmd] )
        subprocess.run([str(target_python), "-c", cmd],
            stdout=open(log_file, 'a'), stderr=subprocess.STDOUT, check=False)

if __name__ == '__main__':
    main()
