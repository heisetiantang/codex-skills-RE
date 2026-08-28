"""
SolidWorks connection utilities
Provides functions to connect to SolidWorks instances
"""
import glob
import os
import time

from sw_preflight import ensure_solidworks_installed, import_com_dependencies

pythoncom, win32com_client, VARIANT = import_com_dependencies()


DOC_TYPE_MAP = {
    "part": 1, "prt": 1, "sldprt": 1,
    "assembly": 2, "asm": 2, "sldasm": 2,
    "drawing": 3, "drw": 3, "slddrw": 3,
}


def get_com_member(obj, attr_name, *args):
    """Compatible accessor for COM members (property or method)."""
    member = getattr(obj, attr_name)
    return member(*args) if callable(member) else member


def create_empty_dispatch_variant():
    """Create empty Dispatch VARIANT for COM calls."""
    return VARIANT(pythoncom.VT_DISPATCH, None)


def normalize_doc_type(doc_type):
    """Normalize document type name."""
    key = str(doc_type).strip().lower().lstrip(".")
    enum_value = DOC_TYPE_MAP.get(key)
    if enum_value is None:
        raise ValueError(f"Unknown doc type: {doc_type}")
    name_map = {1: "part", 2: "assembly", 3: "drawing"}
    return name_map[enum_value], enum_value


def _expand_path(file_path):
    return os.path.abspath(os.path.expandvars(os.path.expanduser(file_path)))


def _ensure_parent_dir(file_path):
    parent = os.path.dirname(_expand_path(file_path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def connect_solidworks(version=None, wait_seconds=5, visible=True):
    """Connect to a SolidWorks instance.

    Args:
        version: SolidWorks year (e.g. 2024), None for auto-detection
        wait_seconds: Wait time after launching new instance
        visible: Whether to show window on new launch

    Returns:
        (sw, model) tuple; model may be None
    """
    ensure_solidworks_installed()
    sw = None

    try:
        sw = win32com_client.GetActiveObject("SldWorks.Application")
        print("Connected to running SolidWorks instance")
    except Exception:
        prog_id = "SldWorks.Application"
        if version:
            revision = (version - 2000) + 8
            prog_id = f"SldWorks.Application.{revision}"
        sw = win32com_client.Dispatch(prog_id)
        sw.Visible = visible
        print(f"Launched new SolidWorks (ProgID: {prog_id})")
        time.sleep(wait_seconds)

    model = sw.ActiveDoc
    if model:
        doc_type = get_com_member(model, "GetType")
        title = get_com_member(model, "GetTitle")
        doc_labels = {1: "Part", 2: "Assembly", 3: "Drawing"}
        print(f"Active doc: {title} (Type: {doc_labels.get(doc_type, 'Unknown')})")
    else:
        print("No active document")

    return sw, model


def get_sw_version(sw):
    rev = get_com_member(sw, "RevisionNumber")
    major = int(rev.split(".")[0])
    year = major - 8 + 2000
    return {"revision": rev, "year": year, "major": major}


def find_template(sw, doc_type="part"):
    """Auto-find SolidWorks document template."""
    doc_type, _ = normalize_doc_type(doc_type)

    type_map = {
        "part": (sw.GetUserPreferenceStringValue(24), "*.prtdot"),
        "assembly": (sw.GetUserPreferenceStringValue(25), "*.asmdot"),
        "drawing": (sw.GetUserPreferenceStringValue(26), "*.drwdot"),
    }

    default_path, pattern = type_map.get(doc_type, type_map["part"])
    if default_path:
        for candidate_root in str(default_path).split(";"):
            candidate_root = _expand_path(candidate_root.strip().strip('"'))
            if not candidate_root:
                continue
            if os.path.isfile(candidate_root):
                return candidate_root
            if os.path.isdir(candidate_root):
                matches = glob.glob(os.path.join(candidate_root, pattern))
                if matches:
                    return matches[0]

    search_dirs = [
        r"C:\ProgramData\SolidWorks\SOLIDWORKS *\templates",
        r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\chinese-simplified",
        r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\english",
    ]
    for search_dir in search_dirs:
        matches = glob.glob(os.path.join(os.path.expandvars(search_dir), pattern))
        if matches:
            return matches[0]

    raise FileNotFoundError(f"Cannot find {doc_type} template file")


def new_document(sw, doc_type="part", template_path=None):
    """Create a new document."""
    doc_type, _ = normalize_doc_type(doc_type)
    if not template_path:
        template_path = find_template(sw, doc_type)
    else:
        template_path = _expand_path(template_path)

    sw.NewDocument(template_path, 0, 0, 0)
    for _ in range(20):
        model = sw.ActiveDoc
        if model is not None:
            break
        time.sleep(0.25)

    if model is None:
        raise RuntimeError("Failed to create document - no active doc returned")

    print(f"New {doc_type} document created")
    return model


def open_document(sw, file_path, read_only=False, silent=False, raise_on_error=False):
    """Open an existing document."""
    file_path = _expand_path(file_path)
    if not os.path.exists(file_path):
        message = f"File not found: {file_path}"
        if raise_on_error:
            raise FileNotFoundError(message)
        print(message)
        return None

    ext = os.path.splitext(file_path)[1].lower()
    type_map = {".sldprt": 1, ".sldasm": 2, ".slddrw": 3,
                ".step": 1, ".stp": 1, ".igs": 1, ".iges": 1}
    doc_type = type_map.get(ext, 1)

    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    options = 2 if read_only else 0
    if silent:
        options |= 1

    model = sw.OpenDoc6(file_path, doc_type, options, "", errors, warnings)
    if model:
        print(f"Opened: {file_path}")
    else:
        message = f"Open failed, errors={errors.value}, warnings={warnings.value}"
        if raise_on_error:
            raise RuntimeError(message)
        print(message)
    return model


def save_document(model, file_path=None):
    """Save a document."""
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

    if file_path:
        file_path = _expand_path(file_path)
        _ensure_parent_dir(file_path)
        success = model.Extension.SaveAs(file_path, 0, 0, create_empty_dispatch_variant(), errors, warnings)
    else:
        success = model.Save3(1, errors, warnings)

    if success:
        print(f"Saved: {file_path or get_com_member(model, 'GetPathName')}")
    else:
        print(f"Save failed, errors={errors.value}, warnings={warnings.value}")
    return bool(success)


def mm(value):
    """Convert millimeters to meters (SolidWorks API unit)."""
    return value / 1000.0


def deg(value):
    """Convert degrees to radians."""
    import math
    return value * math.pi / 180.0



