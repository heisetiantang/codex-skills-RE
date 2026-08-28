"""Quick test: Try different cut methods for SW2024"""
import sys, os
sys.path.insert(0, r"E:\002-自我学习文件\机械\AI机械制图\solidworks-automation-skill\scripts")
import pythoncom, time, glob
from win32com.client import Dispatch, VARIANT

pythoncom.CoInitialize()
sw = Dispatch("SldWorks.Application")
sw.Visible = True
time.sleep(2)

model = sw.ActiveDoc
if model is None:
    templates = glob.glob(r"C:\ProgramData\SolidWorks\SOLIDWORKS *\templates\*.prtdot")
    sw.NewDocument(templates[0], 0, 0, 0)
    time.sleep(2)
    model = sw.ActiveDoc

# Base block
model.ClearSelection2(True)
model.Extension.SelectByID2("上视基准面", "PLANE", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCornerRectangle(-0.06, -0.04, 0, 0.06, 0.04, 0)
model.InsertSketch2(True)
model.ClearSelection2(True)
model.Extension.SelectByID2("草图1", "SKETCH", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.FeatureManager.FeatureExtrusion(True, False, False, False, 0.01, False, 0, False, False, False, False, False, False, False, False, 0, 0, False, False, False)
print("Block OK")

# Hole sketch
model.ClearSelection2(True)
model.Extension.SelectByID2("", "FACE", 0, 0, 0.01, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCircle(0, 0, 0, 0.003, 0, 0)
# Keep sketch OPEN for extrusion (don't toggle)

# Now try extrude cut with sketch still open - FeatureManager uses active sketch
# Instead of FeatureExtrusion2, try InsertCutBlend or use the FeatureManager differently
fm = model.FeatureManager

# Method 1: InsertCutBlend
try:
    fm.InsertCutBlend(False, True, False, 1, 0, 0.01, 0, False)
    print("InsertCutBlend OK")
except Exception as e:
    print(f"InsertCutBlend: {e}")

# Method 2: FeatureCut with sketch active (still in sketch mode)
try:
    # Exit sketch first
    model.InsertSketch2(True)
    model.ClearSelection2(True)
    model.Extension.SelectByID2("草图2", "SKETCH", 0, 0, 0, False, 1, VARIANT(pythoncom.VT_DISPATCH, None), 0)
    
    # FeatureCutTrue
    fm.FeatureCutTrue(True, False, False, 0, 0, 0.01, 0.01,
                      False, False, False, False,
                      0, 0, 0, 0, 0, 0, False)
    print("FeatureCutTrue OK")
except Exception as e:
    print(f"FeatureCutTrue: {e}")

# Method 3: Don't exit sketch, use FeatureExtrusion2 with cut flag
model.ClearSelection2(True)
model.Extension.SelectByID2("", "FACE", 0, 0, 0.01, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCircle(0.02, 0.02, 0, 0.003, 0, 0)

# FeatureExtrusion2 with isCut=True - try all param counts  
try:
    fm.FeatureExtrusion2(True, False, False, 0, 0, 0.01, 0, 0, 
                         False, False, False, 0, 0, False, False, False, False, True, True)
    print("FeatureExtrusion2 19 OK")
except Exception as e:
    print(f"FeatureExtrusion2 19: {e}")

try:
    fm.FeatureExtrusion2(True, False, False, 0, 0, 0.01, 0, 0,
                         False, False, False, 0, 0, False, False, False, False, True, True, False)
    print("FeatureExtrusion2 20 OK")
except Exception as e:
    print(f"FeatureExtrusion2 20: {e}")

try:
    fm.FeatureExtrusion2(True, False, False, 0, 0, 0.01, 0, 0,
                         False, False, False, 0, 0, False, False, False, False, True, True, False, False)
    print("FeatureExtrusion2 21 OK")
except Exception as e:
    print(f"FeatureExtrusion2 21: {e}")

# Method 4: Select sketch, use FeatureExtrusion (the working one), but with cut
model.InsertSketch2(True)  # exit sketch
model.ClearSelection2(True)
model.Extension.SelectByID2("草图3" if model.GetFeatureCount > 2 else "草图2", "SKETCH", 0, 0, 0, False, 1, VARIANT(pythoncom.VT_DISPATCH, None), 0)

# FeatureExtrusion same 20 params but swap some? Actually FeatureExtrusion IS boss. 
# For cut, need FeatureCut. Let's try the specific mark=256 for cut
model.ClearSelection2(True)
# mark 256 = swSelectTypeCut
model.Extension.SelectByID2("草图2", "SKETCH", 0, 0, 0, False, 256, VARIANT(pythoncom.VT_DISPATCH, None), 0)
try:
    fm.FeatureCut(True, False, False, False, 0.01)
    print("FeatureCut 5 OK")
except:
    try:
        fm.FeatureCut(True, False, False, False, 0.01, False, 0)
        print("FeatureCut 7 OK")
    except Exception as e2:
        print(f"FeatureCut: {e2}")

pythoncom.CoUninitialize()
