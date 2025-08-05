import os
import sys
# Use tomllib if available (Python 3.11+), otherwise fall back to tomli
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # For older Python versions
    except ImportError:
        print("Please install tomli for Python < 3.11: pip install tomli")
        sys.exit(1)

#import yaml
import subprocess
from pathlib import Path

def load_builds(config_file):
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    builds = config["builds"]
    python_versions = config.get("pythons", {})
    return builds, python_versions
    #with open(config_file, "r", encoding="utf-8") as f:
    #    return yaml.safe_load(f)["builds"]

def run_build(build, python_versions):
    print(f"\n=== Building WinPython: {build['name']} ===")
    print(build)

    root_dir_for_builds = build["root_dir_for_builds"]
    my_python_target = build["python_target"]
    my_flavor = build["flavor"]
    my_arch = str(build["arch"])
    my_create_installer = build.get("create_installer", "True")
    my_requirements = build.get("requirements", "")
    my_source_dirs = build.get("source_dirs", "")
    my_find_links = build.get("find_links", "")
    my_toolsdirs = build.get("toolsdirs", "")
    #my_install_options = build.get("install_options", "")
    wheelhousereq = build.get("wheelhousereq", "")

    # Get Python release info from TOML [pythons]
    py_target = my_python_target
    vinfo = python_versions.get(py_target, {})
    my_python_target_release = vinfo.get("python_target_release", "")
    my_release = vinfo.get("release", "")
    my_release_level = vinfo.get("my_release_level", "b0")
    mandatory_requirements = vinfo.get("mandatory_requirements", os.path.join(os.getcwd(), "mandatory_requirements.txt"))
 
    # Get Python release info from TOML [pythons] 
    my_constraints = build.get("my_constraints", r"C:\WinP\constraints.txt")
    target_python_exe = build.get("target_python_exe", "python.exe")

    # Build directory logic
    my_basedir = f"{root_dir_for_builds}\\bd{my_python_target}"
    my_WINPYDIRBASE = f"{my_basedir}\\bu{my_flavor}\\WPy{my_arch}-{my_python_target_release}{my_release}{my_release_level}"

    # Build env paths (customize as needed) already defined per the launcher of that script...
 
    my_python_exe = Path(sys.executable)
    my_buildenvi = str(my_python_exe.parent)

    my_archive_dir = os.path.join(os.getcwd(), "WinPython_build_logs")
    os.makedirs(my_archive_dir, exist_ok=True)

    my_requirements_pre = build.get("my_requirements_pre",  mandatory_requirements)

    # Build command
    build_cmd = [
        str(my_python_exe),
        "-m", "winpython.build_winpython",
        "--buildenv", my_buildenvi,
        "--python-target", my_python_target,
        "--release", my_release,
        "--release-level", my_release_level,
        "--winpydirbase", my_WINPYDIRBASE,
        "--flavor", my_flavor,
        "--source_dirs", my_source_dirs,
        "--tools_dirs", my_toolsdirs,
        "--log-dir", my_archive_dir,
        "--mandatory-req", mandatory_requirements,
        "--pre-req", my_requirements_pre,
        "--requirements", my_requirements,
        "--constraints", my_constraints,
        "--find-links", my_find_links,
        "--wheelhousereq", wheelhousereq,
        "--create-installer", my_create_installer,
        #"--install-options", env["my_install_options"],
    ]

    print("Running build command:")
    print(" ".join(build_cmd))
    subprocess.run(build_cmd, cwd=os.getcwd(), check=False)

def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "winpython_buildsNOT.toml"
    builds, python_versions = load_builds(config_file)
    for build in builds:
        run_build(build, python_versions)

if __name__ == "__main__":
    main()
