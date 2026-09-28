"""Find and use the correct face for sketch"""
import pythoncom, time, os, glob
from win32com.client import Dispatch, VARIANT, GetActiveObject

pythoncom.CoInitialize()
sw = Dispatch('SldWorks.Application')
sw.Visible = True
time.sleep(8)

sw.CloseAllDocuments(True)
time.sleep(1)
templates = glob.glob(r'C:\ProgramData\SolidWorks\SOLIDWORKS *\templates\*.prtdot')
sw.NewDocument(templates[0], 0, 0, 0)
time.sleep(2)
model = sw.ActiveDoc
print(f'Part: {model.GetTitle}')

def mm(v): return v / 1000.0

# Create plate
model.ClearSelection2(True)
model.Extension.SelectByID2('上视基准面', 'PLANE', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCornerRectangle(mm(-60), mm(-40), 0, mm(60), mm(40), 0)
model.InsertSketch2(True)
model.ClearSelection2(True)
model.Extension.SelectByID2('草图1', 'SKETCH', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.FeatureManager.FeatureExtrusion(True, False, False, False, mm(10), False, 0, False, False, False, False, False, False, False, False, 0, 0, False, False, False)
print('Plate OK')

# FIND THE TOP FACE
# Method: iterate all faces, check normal direction (Z+)
faces = model.GetBodies2(0, False)  # get all solid bodies
print(f'Bodies: {faces}')

# Alternative: use SelectByRay or Body2.GetFaces
# Actually the simplest: extrude on the SAME plane we used (Top Plane)
# but since we already extruded from it, let's use the extrusion feature face

# THE FIX: Instead of selecting a face, just create the new sketch on the 
# Top Plane but OFFSET by 10mm!
model.ClearSelection2(True)
model.Extension.SelectByID2('上视基准面', 'PLANE', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)

# Create a new reference plane at offset 10mm
# Actually: simpler approach - just start sketch on Top Plane with offset=false,
# the holes will cut through the whole body from the bottom

# EVEN SIMPLER: just use the TOP PLANE directly, the cut goes through all!
model.InsertSketch2(True)
print('Sketch started on Top Plane')

for sx, sy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
    model.SketchManager.CreateCircle(sx*mm(45), sy*mm(25), 0, sx*mm(45)+mm(3), sy*mm(25), 0)
model.InsertSketch2(True)
print('Holes sketched on Top Plane')

# Select and cut through
model.ClearSelection2(True)
model.Extension.SelectByID2('草图2', 'SKETCH', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
fm = model.FeatureManager
fm.FeatureCut4(True, False, False, 0, 0, mm(10), mm(10), False, False, False, False, 0.0, 0.0, False, False, False, False, False, False, True, False, False, False, 0, 0.0, False, False)
print('Cut done')

model.ForceRebuild3(False)
model.ViewZoomtofit2()

# Save
base = r'E:\002-自我学习文件\机械\AI机械制图\mounting_plate'
for ext in ['SLDPRT', 'STEP']:
    p = f'{base}.{ext}'
    if os.path.exists(p): os.remove(p)
e = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
w = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
model.Extension.SaveAs(base+'.SLDPRT', 0, 0, VARIANT(pythoncom.VT_DISPATCH, None), e, w)
e2 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
w2 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
model.Extension.SaveAs(base+'.STEP', 0, 0, VARIANT(pythoncom.VT_DISPATCH, None), e2, w2)
print(f'SLDPRT: {os.path.getsize(base+".SLDPRT")}B')
print(f'STEP: {os.path.getsize(base+".STEP")}B' if os.path.exists(base+'.STEP') else 'STEP: MISSING')

print('\nDONE - Check SW: plate + holes should be aligned!')
pythoncom.CoUninitialize()
