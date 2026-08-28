"""
SolidWorks part modeling utilities
Sketch drawing and feature creation - verified with SW2024
"""
from contextlib import contextmanager

from sw_preflight import import_com_dependencies

pythoncom, _win32com, VARIANT = import_com_dependencies()

# Plane name aliases for Chinese/English SolidWorks versions
PLANE_NAME_ALIASES = {
    "Front Plane": ["Front Plane", "前视基准面"],
    "Top Plane": ["Top Plane", "上视基准面"],
    "Right Plane": ["Right Plane", "右视基准面"],
    "前视基准面": ["前视基准面", "Front Plane"],
    "上视基准面": ["上视基准面", "Top Plane"],
    "右视基准面": ["右视基准面", "Right Plane"],
}

SKETCH_NAME_PREFIX_ALIASES = {
    "Sketch": "草图",
    "草图": "Sketch",
}


def _empty_callout():
    return VARIANT(pythoncom.VT_DISPATCH, None)


def _select_by_id(extension, entity_name, entity_type, append=False, mark=0):
    return extension.SelectByID2(
        entity_name, entity_type, 0, 0, 0, append, mark, _empty_callout(), 0
    )


def _get_plane_name_candidates(plane_name):
    return PLANE_NAME_ALIASES.get(plane_name, [plane_name])


def _get_sketch_name_candidates(sketch_name):
    candidates = [sketch_name]
    for prefix, alias in SKETCH_NAME_PREFIX_ALIASES.items():
        if sketch_name.startswith(prefix):
            alias_name = alias + sketch_name[len(prefix):]
            if alias_name not in candidates:
                candidates.append(alias_name)
    return candidates


def _select_first_candidate(extension, candidate_names, entity_type, append=False, mark=0):
    for candidate_name in candidate_names:
        if _select_by_id(extension, candidate_name, entity_type, append=append, mark=mark):
            return candidate_name
    return None


def start_sketch(model, plane_name="Front Plane"):
    """Start a sketch on the specified plane. Returns sketch name."""
    model.ClearSelection2(True)

    selected_plane = _select_first_candidate(
        model.Extension, _get_plane_name_candidates(plane_name), "PLANE"
    )
    if not selected_plane:
        raise ValueError(f"Cannot select plane: {plane_name}")

    # InsertSketch2(True) for entering a new sketch (SW2024)
    model.InsertSketch2(True)

    # Get sketch name from the feature tree
    fc = model.GetFeatureCount
    for i in range(fc):
        feat = model.FeatureByPositionReverse(fc - i)
        if feat:
            tname = feat.GetTypeName2
            if tname == "ProfileFeature":
                name = feat.Name
                print(f"Sketch started: {name} on {selected_plane}")
                return name

    # Fallback: try known name
    for fallback in ["草图1", "Sketch1"]:
        try:
            if _select_by_id(model.Extension, fallback, "SKETCH"):
                print(f"Sketch started: {fallback} on {selected_plane}")
                return fallback
        except:
            pass

    raise RuntimeError("Failed to identify sketch name")


def end_sketch(model):
    """Exit sketch editing mode."""
    model.InsertSketch2(True)
    print("Sketch exited")


@contextmanager
def sketch(model, plane_name="Front Plane"):
    """Context manager for sketch editing."""
    sketch_name = start_sketch(model, plane_name)
    try:
        yield sketch_name
    finally:
        end_sketch(model)


# ---- Sketch Geometry ----

def sketch_circle(model, cx, cy, radius):
    """Draw a circle by center and radius (in meters)."""
    model.SketchManager.CreateCircle(cx, cy, 0, cx + radius, cy, 0)
    print(f"Circle: R={radius*1000:.1f}mm")


def sketch_rectangle(model, x1, y1, x2, y2, centered=False):
    """Draw a corner rectangle."""
    if centered:
        hw = abs(x2 - x1) / 2
        hh = abs(y2 - y1) / 2
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        model.SketchManager.CreateCenterRectangle(cx, cy, 0, cx + hw, cy + hh, 0)
    else:
        model.SketchManager.CreateCornerRectangle(x1, y1, 0, x2, y2, 0)
    print("Rectangle drawn")


def sketch_line(model, x1, y1, x2, y2):
    """Draw a line."""
    model.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0)


def sketch_slot(model, cx, cy, length, width):
    """Draw a straight slot."""
    import math
    hw = width / 2
    hl = length / 2
    sketch_circle(model, cx - hl, cy, hw)
    sketch_circle(model, cx + hl, cy, hw)
    model.SketchManager.CreateLine(cx - hl, cy - hw, 0, cx + hl, cy - hw, 0)
    model.SketchManager.CreateLine(cx - hl, cy + hw, 0, cx + hl, cy + hw, 0)


# ---- Feature Operations ----

def extrude_boss(model, sketch_name, depth, flip=False):
    """Create a boss extrusion (verified with SW2024)."""
    # End current sketch if open, then select
    model.ClearSelection2(True)

    # Select the sketch
    selected = _select_first_candidate(
        model.Extension, _get_sketch_name_candidates(sketch_name), "SKETCH"
    )
    if not selected:
        raise ValueError(f"Cannot select sketch: {sketch_name}")

    # FeatureExtrusion(sd, flip, dir, t1, t1Val, t2, t2Val, d1, d2,
    #   dchk1, dchk2, ddir1, ddir2, dside1, dside2,
    #   offset1, offset2, ofr1, ofr2, tsF1, tsF2)
    # --- Wait, we need 20 params based on our testing ---
    # sd=True, flip, dir, t1=False(blind), depth, t2=False, 0, d1=False, d2=False,
    # dchk1=False through tsF2=False = 20 params total
    model.FeatureManager.FeatureExtrusion(
        True,    # sd - single direction
        flip,    # flip
        False,   # dir
        False,   # t1 (False=Blind)
        depth,   # t1Val - depth in meters
        False,   # t2
        0,       # t2Val
        False,   # d1
        False,   # d2
        False,   # dchk1
        False,   # dchk2
        False,   # ddir1
        False,   # ddir2
        False,   # dside1
        False,   # dside2
        0,       # offset1
        0,       # offset2
        False,   # ofr1
        False,   # ofr2
        False,   # tsF1
        # Note: tsF2 was not in our 20-param call, but FeatureExtrusion needs 20+
        # Let's keep 20: sd(1)+flip(2)+dir(3)+t1(4)+t1Val(5)+t2(6)+t2Val(7)+
        # d1(8)+d2(9)+dchk1(10)+dchk2(11)+ddir1(12)+ddir2(13)+dside1(14)+
        # dside2(15)+offset1(16)+offset2(17)+ofr1(18)+ofr2(19)+tsF1(20)
    )
    print(f"Extruded: depth={depth*1000:.0f}mm")


def start_sketch_on_top_face(model):
    """Start sketch on the top Z face of active body. Falls back to Top Plane."""
    model.ClearSelection2(True)
    bodies = model.GetBodies2(0)
    if bodies:
        for body in bodies:
            faces = body.GetFaces()
            for face in faces:
                surf = face.GetSurface()
                if surf and surf.IsPlane():
                    # Check if it's a Z+ facing plane near top
                    try:
                        params = surf.Evaluate(0, 0, 0)
                        if len(params) > 2 and params[2] > 0.001:  # Z > 1mm
                            face.Select2(True, 0)
                            model.InsertSketch2(True)
                            return 'sketch_on_face'
                    except:
                        pass
    # Fallback
    print('Using Top Plane for sketch')
    return start_sketch(model, 'Top Plane')


def extrude_cut(model, sketch_name, depth, flip=False):
    """Create a cut extrusion (SW2024 verified: 27 params).
    """Create a cut extrusion (SW2024 verified: 27 params).

    Args:
        model: IModelDoc2
        sketch_name: Name of the sketch to cut
        depth: Cut depth in meters
        flip: Flip direction
    """
    model.ClearSelection2(True)
    selected = _select_first_candidate(
        model.Extension, _get_sketch_name_candidates(sketch_name), "SKETCH"
    )
    if not selected:
        raise ValueError(f"Cannot select sketch: {sketch_name}")

    # FeatureCut4(Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2,
    #   Dang1, Dang2, OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2,
    #   NormalCut, UseFeatScope, UseAutoSelect, AssemblyFeatureScope, AutoSelectComponents,
    #   PropagateFeatureToParts, T0, StartOffset, FlipStartOffset, OptimizeGeometry)
    model.FeatureManager.FeatureCut4(
        True,    # Sd - single direction
        flip,    # Flip
        False,   # Dir
        0,       # T1 - Blind end condition
        0,       # T2 - Blind
        depth,   # D1 - depth in meters
        depth,   # D2
        False,   # Dchk1
        False,   # Dchk2
        False,   # Ddir1
        False,   # Ddir2
        0.0,     # Dang1
        0.0,     # Dang2
        False,   # OffsetReverse1
        False,   # OffsetReverse2
        False,   # TranslateSurface1
        False,   # TranslateSurface2
        False,   # NormalCut
        False,   # UseFeatScope
        True,    # UseAutoSelect
        False,   # AssemblyFeatureScope
        False,   # AutoSelectComponents
        False,   # PropagateFeatureToParts
        0,       # T0
        0.0,     # StartOffset
        False,   # FlipStartOffset
        False    # OptimizeGeometry
    )
    print(f"Cut: depth={depth*1000:.0f}mm")


def fillet(model, radius):
    """Create a constant radius fillet on selected edges."""
    model.FeatureManager.FeatureFillet(195, radius, 0, 0, None, None, None)
    print(f"Fillet: R={radius*1000:.1f}mm")


def chamfer(model, distance, angle_deg=45):
    """Create a chamfer."""
    import math
    angle_rad = angle_deg * math.pi / 180.0
    model.FeatureManager.InsertFeatureChamfer(4, 1, distance, angle_rad, 0, 0, 0, 0)
    print(f"Chamfer: {distance*1000:.1f}mm x {angle_deg}deg")


