"""Test: Create a mounting plate with 4 corner holes"""
import sys, os
sys.path.insert(0, r"E:\002-自我学习文件\机械\AI机械制图\solidworks-automation-skill\scripts")
import pythoncom
from win32com.client import VARIANT
from sw_connect import connect_solidworks, mm, new_document, save_document
from sw_part import (
    start_sketch, sketch_rectangle, sketch_circle,
    extrude_boss, fillet
)
from sw_export import export_to_step

pythoncom.CoInitialize()

print("=" * 50)
print("  Mounting Plate: 120x80x10mm + 4x phi6 holes + R5 fillets")
print("=" * 50)

sw, model = connect_solidworks(visible=True)
if model is None:
    model = new_document(sw, "part")

# Step 1: Base plate on Top Plane
print("\n[1/3] Base plate 120x80x10mm...")
sk1 = start_sketch(model, "Top Plane")
sketch_rectangle(model, mm(-60), mm(-40), mm(60), mm(40), centered=True)
extrude_boss(model, sk1, mm(10))

# Step 2: 4 corner holes on the TOP FACE of the extrusion
print("\n[2/3] Drilling 4 corner holes...")
model.ClearSelection2(True)

# Select the top face of the body
model.Extension.SelectByID2("", "FACE", 0, 0, mm(10), False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)

# Draw 4 circles
hx, hy = mm(40), mm(30)
for sx, sy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
    sketch_circle(model, sx * hx, sy * hy, mm(3))

# Toggle sketch to exit editing
model.InsertSketch2(True)

# Get the new sketch name
fc = model.GetFeatureCount
sk2_name = None
for i in range(fc):
    feat = model.FeatureByPositionReverse(fc - i)
    if feat and feat.GetTypeName2 == "ProfileFeature":
        n = feat.Name
        if n != sk1:
            sk2_name = n
            break

if not sk2_name:
    sk2_name = "草图2"

print(f"  Sketch: {sk2_name}, 4 circles drawn")

# Select sketch and use FeatureCut4
model.ClearSelection2(True)
model.Extension.SelectByID2(sk2_name, "SKETCH", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)

# Try FeatureCut4 with different param counts
fm = model.FeatureManager
cut_ok = False
for n in range(25, 10, -1):
    try:
        args = [True, False, False, 0, 0, mm(10), mm(10),
                False, False, False, False,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        fm.FeatureCut4(*args[:n])
        print(f"  FeatureCut4({n} params) OK")
        cut_ok = True
        break
    except Exception as e:
        pass

if not cut_ok:
    # Fallback: use FeatureCut3
    for n in range(20, 5, -1):
        try:
            args = [True, False, False, 0, 0, mm(10), mm(10),
                    False, False, False, False, False, False,
                    0, 0, False, False]
            fm.FeatureCut3(*args[:n])
            print(f"  FeatureCut3({n} params) OK")
            cut_ok = True
            break
        except:
            pass

if not cut_ok:
    print("  WARNING: Cut failed, trying alternative...")
    # Try: exit sketch, use InsertCutBlend
    model.ClearSelection2(True)
    model.Extension.SelectByID2(sk2_name, "SKETCH", 0, 0, 0, False, 1, VARIANT(pythoncom.VT_DISPATCH, None), 0)
    # FeatureCut is simplest
    try:
        fm.FeatureCut(True, False, False, 0, 0, mm(10), mm(10),
                      False, False, False, False, False, False, False, False,
                      0, 0, 0, 0, False, False, False)
        print("  FeatureCut(21) OK")
    except:
        print("  All cut methods failed - holes may need manual creation")

# Step 3: Corner fillets R5
print("\n[3/3] R5 fillets on 4 corners...")
model.ClearSelection2(True)
corners = [
    (mm(-60)+mm(2), mm(-40)+mm(2)),
    (mm(60)-mm(2), mm(-40)+mm(2)),
    (mm(-60)+mm(2), mm(40)-mm(2)),
    (mm(60)-mm(2), mm(40)-mm(2)),
]
for i, (ex, ey) in enumerate(corners):
    model.Extension.SelectByID2("", "EDGE", ex, ey, mm(5), i > 0, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)

fillet(model, mm(5))

# Rebuild and zoom
model.ForceRebuild3(False)
model.ViewZoomtofit2()

# Save
base = r"E:\002-自我学习文件\机械\AI机械制图\mounting_plate"
for p in [base+".SLDPRT", base+".STEP"]:
    try: os.remove(p)
    except: pass

save_document(model, base+".SLDPRT")
export_to_step(model, base+".STEP")

sld_size = os.path.getsize(base+".SLDPRT") if os.path.exists(base+".SLDPRT") else 0
stp_size = os.path.getsize(base+".STEP") if os.path.exists(base+".STEP") else 0
print(f"\n  SLDPRT: {sld_size}B")
print(f"  STEP:   {stp_size}B")
print("\nDone!")
pythoncom.CoUninitialize()
