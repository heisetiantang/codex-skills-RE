"""Visual step-by-step SW demo - one continuous session"""
import sys, os, glob
sys.path.insert(0, r"E:\002-自我学习文件\机械\AI机械制图\solidworks-automation-skill\scripts")
import pythoncom, time
from win32com.client import Dispatch, VARIANT, GetActiveObject

pythoncom.CoInitialize()

# Try connect first, then launch
try:
    sw = GetActiveObject("SldWorks.Application")
    print("[OK] Connected to running SW")
except:
    sw = Dispatch("SldWorks.Application")
    sw.Visible = True
    sw.CommandInProgress = True
    time.sleep(5)
    print("[OK] Launched SW")

print(f"SW Revision: {sw.RevisionNumber}")

# Keep SW visible and bring to front
sw.Visible = True
time.sleep(1)

# Close any existing documents
try:
    sw.CloseAllDocuments(True)
    time.sleep(1)
except:
    pass

# === STEP 1: New Part ===
input("\n[Step 1/4] Press ENTER to create a new part...")
templates = glob.glob(r"C:\ProgramData\SolidWorks\SOLIDWORKS *\templates\*.prtdot")
sw.NewDocument(templates[0], 0, 0, 0)
time.sleep(2)
model = sw.ActiveDoc
print(f"  Created: {model.GetTitle}")
sw.Visible = True

# === STEP 2: Draw rectangle sketch ===
input("\n[Step 2/4] Press ENTER to draw 80x60mm rectangle...")
model.ClearSelection2(True)
model.Extension.SelectByID2("上视基准面", "PLANE", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCornerRectangle(-0.04, -0.03, 0, 0.04, 0.03, 0)
print("  Rectangle 80x60mm drawn!")

# === STEP 3: Extrude ===
input("\n[Step 3/4] Press ENTER to extrude 15mm...")
model.InsertSketch2(True)
model.ClearSelection2(True)
model.Extension.SelectByID2("草图1", "SKETCH", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.FeatureManager.FeatureExtrusion(
    True, False, False, False, 0.015, False, 0,
    False, False, False, False, False, False,
    False, False, 0, 0, False, False, False
)
model.ViewZoomtofit2()
print("  Extruded 15mm!")

# === STEP 4: 2 holes on top face ===
input("\n[Step 4/4] Press ENTER to drill 2x phi8mm holes...")
model.ClearSelection2(True)
model.Extension.SelectByID2("", "FACE", 0, 0, 0.015, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCircle(-0.03, -0.02, 0, -0.03+0.004, -0.02, 0)
model.SketchManager.CreateCircle(0.03, -0.02, 0, 0.03+0.004, -0.02, 0)
print("  2x 8mm holes sketched")
model.InsertSketch2(True)

# Select sketch for cut
model.ClearSelection2(True)
model.Extension.SelectByID2("草图2", "SKETCH", 0, 0, 0, False, 1, VARIANT(pythoncom.VT_DISPATCH, None), 0)

# Try FeatureCut through different approaches
fm = model.FeatureManager
cut_ok = False

# Approach 1: FeatureCut3 with all False bools
for n in range(22, 4, -1):
    try:
        args = [True]*n
        fm.FeatureCut3(*args)
        print(f"  Hole cut with FeatureCut3({n})!")
        cut_ok = True
        break
    except:
        pass

# Approach 2: FeatureCut4  
if not cut_ok:
    for n in range(24, 4, -1):
        try:
            args = [True]*n
            fm.FeatureCut4(*args)
            print(f"  Hole cut with FeatureCut4({n})!")
            cut_ok = True
            break
        except:
            pass

# Approach 3: FeatureCut  
if not cut_ok:
    for n in range(24, 4, -1):
        try:
            args = [True]*n
            fm.FeatureCut(*args)
            print(f"  Hole cut with FeatureCut({n})!")
            cut_ok = True
            break
        except:
            pass

# Approach 4: InsertCutExtrude
if not cut_ok:
    try:
        fm.InsertCutExtrude(True, False, False, 0, 0, 0.015, 0.015,
                            False, False, False, False,
                            0, 0, 0, 0, 0, 0, False)
        print("  Hole cut with InsertCutExtrude!")
        cut_ok = True
    except:
        pass

# Approach 5: Use simple hole wizard
if not cut_ok:
    try:
        fm.HoleWizard(2, 0, 0, 0, 0.004, 0.015, 0.0, 0.0, 0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0, 0.0, 0.0, False, False, False, False,
                      False, False, False, False, False)
        print("  Hole cut with HoleWizard!")
        cut_ok = True
    except:
        pass

if not cut_ok:
    print("  WARNING: Auto-cut failed. SW still shows the sketch - you can manually cut.")

model.ViewZoomtofit2()

# Save
outPath = r"E:\002-自我学习文件\机械\AI机械制图\demo_block.SLDPRT"
if os.path.exists(outPath): os.remove(outPath)
errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
model.Extension.SaveAs(outPath, 0, 0, VARIANT(pythoncom.VT_DISPATCH, None), errors, warnings)
print(f"\n  Saved: {outPath}")

pythoncom.CoUninitialize()
print("\n=== DONE ===")
