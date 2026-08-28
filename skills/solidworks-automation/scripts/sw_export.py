"""
SolidWorks file export utilities
"""
import os

try:
    from .sw_preflight import import_com_dependencies
except ImportError:
    from sw_preflight import import_com_dependencies

pythoncom, _win32com, VARIANT = import_com_dependencies()


def _ensure_dir(file_path):
    parent = os.path.dirname(os.path.abspath(file_path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def export_to_step(model, output_path, version=203):
    """Export to STEP format."""
    _ensure_dir(output_path)
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    success = model.Extension.SaveAs(
        output_path, version, 0, None, errors, warnings)
    if success:
        print(f"STEP exported: {output_path}")
    else:
        print(f"STEP export failed: errors={errors.value}, warnings={warnings.value}")
    return bool(success)


def export_to_stl(model, output_path, quality="fine"):
    """Export to STL format."""
    _ensure_dir(output_path)
    quality_map = {"coarse": 0, "fine": 1, "custom": 2}
    qv = quality_map.get(quality, 1)
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    success = model.Extension.SaveAs(
        output_path, 4, qv, None, errors, warnings)
    if success:
        print(f"STL exported: {output_path}")
    else:
        print(f"STL export failed: errors={errors.value}, warnings={warnings.value}")
    return bool(success)


def export_to_iges(model, output_path):
    """Export to IGES format."""
    _ensure_dir(output_path)
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    success = model.Extension.SaveAs(
        output_path, 5, 0, None, errors, warnings)
    if success:
        print(f"IGES exported: {output_path}")
    return bool(success)


def export_to_pdf(model, output_path):
    """Export drawing to PDF."""
    _ensure_dir(output_path)
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    success = model.Extension.SaveAs(
        output_path, 2, 0, None, errors, warnings)
    if success:
        print(f"PDF exported: {output_path}")
    return bool(success)


def export_to_dxf(model, output_path):
    """Export to DXF format."""
    _ensure_dir(output_path)
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    success = model.Extension.SaveAs(
        output_path, 6, 0, None, errors, warnings)
    if success:
        print(f"DXF exported: {output_path}")
    return bool(success)
