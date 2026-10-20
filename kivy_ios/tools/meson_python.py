import sys
import json
import subprocess
import importlib.util
from os.path import join
from glob import glob


class C:
    TARGET_PYTHON_PREFIX = globals().get("TARGET_PYTHON_PREFIX")
    PYTHON_MAJOR_VERSION = globals().get("PYTHON_MAJOR_VERSION", sys.version_info.major)
    PYTHON_MINOR_VERSION = globals().get("PYTHON_MINOR_VERSION", sys.version_info.minor)
    PLATFORM_TAG = globals().get("PLATFORM_TAG", sys.platform)
    PYTHON_SUFFIX = globals().get("PYTHON_SUFFIX", "")


def handle_python_info():
    prefix = C.TARGET_PYTHON_PREFIX
    ver_python = f"python{C.PYTHON_MAJOR_VERSION}.{C.PYTHON_MINOR_VERSION}"

    sysconfig_files = glob(join(prefix, f"lib/{ver_python}/_sysconfigdata*.py"))
    if not sysconfig_files:
        sysconfig_files = glob(join(prefix, f"lib/{ver_python}/config-*/_sysconfigdata*.py"))

    variables = {}
    if sysconfig_files:
        try:
            spec = importlib.util.spec_from_file_location("_target_cfg", sysconfig_files[0])
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)
            variables = getattr(cfg, "build_time_vars", {})
        except Exception:
            pass

    site_path = join(prefix, f"lib/{ver_python}/site-packages")

    target_paths = {
        "stdlib": join(prefix, f"lib/{ver_python}"),
        "platstdlib": join(prefix, f"lib/{ver_python}"),
        "purelib": site_path,
        "platlib": site_path,
        "include": join(prefix, f"include/{ver_python}"),
        "platinclude": join(prefix, f"include/{ver_python}"),
        "scripts": join(prefix, "bin"),
        "data": prefix,
    }

    install_paths = {
        "stdlib": f"/lib/{ver_python}",
        "platstdlib": f"/lib/{ver_python}",
        "purelib": f"/lib/{ver_python}/site-packages",
        "platlib": f"/lib/{ver_python}/site-packages",
        "include": f"/include/{ver_python}",
        "platinclude": f"/include/{ver_python}",
        "scripts": "/bin",
        "data": ".",
    }

    suffix = variables.get("EXT_SUFFIX") or C.PYTHON_SUFFIX
    if suffix:
        try:
            major = int(C.PYTHON_MAJOR_VERSION)
            minor = int(C.PYTHON_MINOR_VERSION)
            if major >= 3 and minor >= 8:
                suffix = suffix.replace(f"{major}{minor}m", f"{major}{minor}")
        except Exception:
            pass

    print(
        json.dumps(
            {
                "variables": variables,
                "paths": target_paths,
                "sysconfig_paths": target_paths,
                "install_paths": install_paths,
                "version": f"{C.PYTHON_MAJOR_VERSION}.{C.PYTHON_MINOR_VERSION}",
                "platform": C.PLATFORM_TAG,
                "is_pypy": False,
                "is_venv": False,
                "link_libpython": False,
                "suffix": suffix,
                "limited_api_suffix": ".abi3.so",
                "is_freethreaded": False,
            }
        )
    )


WHITELIST = {
    "python_info.py": handle_python_info,
}


args = sys.argv[1:]

if args:
    cmd = args[0]
    name = cmd.split("/")[-1]

    if name in WHITELIST:
        sys.exit(WHITELIST[name]())

sys.exit(subprocess.run([sys.executable] + args).returncode)
