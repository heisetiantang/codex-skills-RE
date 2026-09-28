"""
SolidWorks Friendly Session API - adapted for local environment
"""
from pathlib import Path
import os

from sw_connect import connect_solidworks, new_document, open_document, save_document

EXPORTERS = {}

# Lazy import sw_export to avoid circular dependency
def _get_exporters():
    if not EXPORTERS:
        try:
            from sw_export import (
                export_to_dxf, export_to_iges, export_to_pdf,
                export_to_stl, export_to_step
            )
            EXPORTERS.update({
                ".step": export_to_step, ".stp": export_to_step,
                ".stl": export_to_stl, ".iges": export_to_iges,
                ".igs": export_to_iges, ".pdf": export_to_pdf,
                ".dxf": export_to_dxf, ".dwg": export_to_dxf,
            })
        except ImportError:
            pass
    return EXPORTERS


class SolidWorksSession:
    """SolidWorks automation session."""

    def __init__(self, version=None, wait_seconds=5, visible=True):
        self.sw, self.model = connect_solidworks(
            version=version, wait_seconds=wait_seconds, visible=visible)

    @property
    def active_doc(self):
        self.model = self.sw.ActiveDoc
        return self.model

    def new(self, doc_type="part", template_path=None):
        self.model = new_document(self.sw, doc_type=doc_type, template_path=template_path)
        return self.model

    def new_part(self, template_path=None):
        return self.new("part", template_path=template_path)

    def new_assembly(self, template_path=None):
        return self.new("assembly", template_path=template_path)

    def new_drawing(self, template_path=None):
        return self.new("drawing", template_path=template_path)

    def open(self, file_path, read_only=False, silent=False, raise_on_error=True):
        self.model = open_document(
            self.sw, file_path, read_only=read_only,
            silent=silent, raise_on_error=raise_on_error)
        return self.model

    def save(self, model=None, file_path=None):
        model = model or self.active_doc
        if model is None:
            raise RuntimeError("No active document to save")
        return save_document(model, file_path=file_path)

    def export(self, model=None, output_path=None, format_ext=None, **kwargs):
        model = model or self.active_doc
        if model is None:
            raise RuntimeError("No active document to export")
        if not output_path:
            raise ValueError("output_path required")
        output = Path(os.path.expandvars(str(output_path))).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        ext = (format_ext or output.suffix).lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        exporters = _get_exporters()
        exporter = exporters.get(ext)
        if exporter is None:
            raise ValueError(f"Unsupported export format: {ext}")
        return exporter(model, str(output), **kwargs)

    def close(self, model=None, title=None):
        if title is None:
            model = model or self.active_doc
            if model is None:
                return False
            title = model.GetTitle()
        self.sw.CloseDoc(title)
        if self.model and self.model.GetTitle() == title:
            self.model = self.sw.ActiveDoc
        return True


def session(version=None, wait_seconds=5, visible=True):
    return SolidWorksSession(version=version, wait_seconds=wait_seconds, visible=visible)
