import pythoncom, time, glob
from win32com.client import Dispatch, VARIANT, GetActiveObject

pythoncom.CoInitialize()

# Launch SW
try:
    sw = GetActiveObject("SldWorks.Application")
except:
    sw = Dispatch("SldWorks.Application")

sw.Visible = True
sw.CommandInProgress = True
time.sleep(3)
print(f"SW running: Rev {sw.RevisionNumber}")

# Close old docs
try: sw.CloseAllDocuments(True)
except: pass
time.sleep(1)

# New part
templates = glob.glob(r"C:\ProgramData\SolidWorks\SOLIDWORKS *\templates\*.prtdot")
sw.NewDocument(templates[0], 0, 0, 0)
time.sleep(2)
model = sw.ActiveDoc
print(f"New part: {model.GetTitle}")
print("SW window should show a blank part!")

# Draw rectangle
model.ClearSelection2(True)
model.Extension.SelectByID2("上视基准面", "PLANE", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCornerRectangle(-0.04, -0.03, 0, 0.04, 0.03, 0)
print("Rectangle 80x60mm drawn - LOOK AT SW!")

# Extrude
model.InsertSketch2(True)
model.ClearSelection2(True)
model.Extension.SelectByID2("草图1", "SKETCH", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.FeatureManager.FeatureExtrusion(
    True, False, False, False, 0.015, False, 0,
    False, False, False, False, False, False,
    False, False, 0, 0, False, False, False
)
model.ViewZoomtofit2()
print("Extruded 15mm - LOOK AT SW!")

# Sketch 2 holes on top face
model.ClearSelection2(True)
model.Extension.SelectByID2("", "FACE", 0, 0, 0.015, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCircle(-0.03, -0.02, 0, -0.026, -0.02, 0)
model.SketchManager.CreateCircle(0.03, -0.02, 0, 0.034, -0.02, 0)
print("2 holes sketched - LOOK AT SW!")

# Save
import os
outPath = r"E:\002-自我学习文件\机械\AI机械制图\demo_block.SLDPRT"
if os.path.exists(outPath): os.remove(outPath)
err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
warn = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
model.Extension.SaveAs(outPath, 0, 0, VARIANT(pythoncom.VT_DISPATCH, None), err, warn)
print(f"Saved: {outPath} ({os.path.getsize(outPath)}B)")

# KEEP SW OPEN - DON'T CoUninitialize
# Let it persist for visual inspection
print("\n=== SW WINDOW IS OPEN, YOU CAN SEE THE PART ===")
print("(Press Ctrl+C in terminal to close when done)")
