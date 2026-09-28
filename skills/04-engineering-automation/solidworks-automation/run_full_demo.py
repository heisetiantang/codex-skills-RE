"""Final: Mounting plate + STEP export"""
import subprocess, time, os, glob, pythoncom
from win32com.client import Dispatch, VARIANT, GetActiveObject

subprocess.run(['taskkill', '/F', '/IM', 'SLDWORKS.exe'], capture_output=True)
time.sleep(3)
subprocess.Popen(['E:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS\\SLDWORKS.exe'])
time.sleep(20)

pythoncom.CoInitialize()
sw = GetActiveObject('SldWorks.Application')
sw.Visible = True
print(f'SW Rev {sw.RevisionNumber}')

sw.CloseAllDocuments(True)
time.sleep(1)
templates = glob.glob(r'C:\ProgramData\SolidWorks\SOLIDWORKS *\templates\*.prtdot')
sw.NewDocument(templates[0], 0, 0, 0)
time.sleep(2)
model = sw.ActiveDoc
print(f'Part: {model.GetTitle}')

def mm(v): return v / 1000.0

# === 1. Plate 120x80x10 ===
print('[1] Plate...')
model.ClearSelection2(True)
model.Extension.SelectByID2('上视基准面', 'PLANE', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCornerRectangle(mm(-60), mm(-40), 0, mm(60), mm(40), 0)
model.InsertSketch2(True)
model.ClearSelection2(True)
model.Extension.SelectByID2('草图1', 'SKETCH', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.FeatureManager.FeatureExtrusion(True, False, False, False, mm(10), False, 0, False, False, False, False, False, False, False, False, 0, 0, False, False, False)

# === 2. 4 corner holes ===
print('[2] Holes...')
model.ClearSelection2(True)
model.Extension.SelectByID2('', 'FACE', 0, 0, mm(10), False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
hx, hy = mm(45), mm(25)  # 15mm from edges
for sx, sy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
    model.SketchManager.CreateCircle(sx*hx, sy*hy, 0, sx*hx+mm(3), sy*hy, 0)
model.InsertSketch2(True)
model.ClearSelection2(True)
model.Extension.SelectByID2('草图2', 'SKETCH', 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
fm = model.FeatureManager
fm.FeatureCut4(True, False, False, 0, 0, mm(10), mm(10), False, False, False, False, 0.0, 0.0, False, False, False, False, False, False, True, False, False, False, 0, 0.0, False, False)

# === 3. R5 fillets ===
print('[3] Fillets...')
model.ClearSelection2(True)
for cx, cy in [(mm(-60), mm(-40)), (mm(60), mm(-40)), (mm(-60), mm(40)), (mm(60), mm(40))]:
    model.Extension.SelectByID2('', 'EDGE', cx, cy, mm(5), True, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
fm.FeatureFillet(195, mm(5), 0, 0, None, None, None)

model.ForceRebuild3(False)
model.ViewZoomtofit2()

# === Save ===
outDir = r'E:\002-自我学习文件\机械\AI机械制图'
base = outDir + r'\mounting_plate'
for f in [base+'.SLDPRT', base+'.STEP']:
    if os.path.exists(f): os.remove(f)

# SLDPRT
e1 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
w1 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
model.Extension.SaveAs(base+'.SLDPRT', 0, 0, VARIANT(pythoncom.VT_DISPATCH, None), e1, w1)

# STEP - use version=0 (current) plus explicit STEP type
# SaveAs with version=1 for STEP (swSTEP_AP203 = 1)
e2 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
w2 = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
model.Extension.SaveAs(base+'.STEP', 1, 0, VARIANT(pythoncom.VT_DISPATCH, None), e2, w2)

for ext in ['SLDPRT', 'STEP']:
    p = f'{base}.{ext}'
    print(f'{ext}: {os.path.getsize(p)}B' if os.path.exists(p) else f'{ext}: MISSING')

print('\n=== FINISHED - Check SW window! ===')
print('120x80x10 plate + 4x phi6 holes + R5 fillets')
