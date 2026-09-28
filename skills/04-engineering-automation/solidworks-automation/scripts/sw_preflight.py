"""
SolidWorks preflight check - simplified for local use
Only checks pywin32 (already installed) and SolidWorks presence
"""
import argparse
import glob
import importlib
import os
import platform
import sys


class SolidWorksNotInstalledError(RuntimeError):
    """SolidWorks not detected."""


def _module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ModuleNotFoundError:
        return False


def solidworks_installed() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg
        winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, r"SldWorks.Application\CLSID")
        return True
    except Exception:
        pass
    patterns = [
        r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
        r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS*\SLDWORKS.exe",
    ]
    for pattern in patterns:
        if glob.glob(os.path.expandvars(pattern)):
            return True
    return False


def ensure_solidworks_installed() -> None:
    if solidworks_installed():
        return
    raise SolidWorksNotInstalledError(
        "SolidWorks not detected. Please install SolidWorks and run it at least once."
    )


def import_com_dependencies():
    """Import pywin32 COM dependencies."""
    if not _module_available("pythoncom") or not _module_available("win32com.client"):
        raise ModuleNotFoundError(
            "pywin32 not found. Install with: pip install pywin32"
        )
    pythoncom = importlib.import_module("pythoncom")
    client = importlib.import_module("win32com.client")
    return pythoncom, client, client.VARIANT


def run_preflight(check_solidworks=True):
    if check_solidworks:
        ensure_solidworks_installed()
    import_com_dependencies()
    print("SolidWorks skill preflight OK - pywin32 ready, SolidWorks detected.")
    return True


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--no-solidworks-check", action="store_true")
    args = p.parse_args()
    try:
        run_preflight(check_solidworks=not args.no_solidworks_check)
    except SolidWorksNotInstalledError as e:
        print(e, file=sys.stderr)
        sys.exit(3)
    except ModuleNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(2)
