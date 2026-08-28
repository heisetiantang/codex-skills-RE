"""Bring SW to front and verify basic operations"""
import sys, os
sys.path.insert(0, r"E:\002-自我学习文件\机械\AI机械制图\solidworks-automation-skill\scripts")
import pythoncom, time, glob
from win32com.client import Dispatch, VARIANT

pythoncom.CoInitialize()

# Try to get already running instance first
try:
    from win32com.client import GetActiveObject
    sw = GetActiveObject("SldWorks.Application")
    print("Found running SW!")
except:
    sw = Dispatch("SldWorks.Application")
    print("Started new SW")

sw.Visible = True

# Bring SW window to front
try:
    import win32gui, win32con
    hwnd = sw.Frame().GetHWND() if hasattr(sw, 'Frame') else None
    if not hwnd:
        # Search for SW window
        def enum_callback(hwnd, sw_hwnds):
            if 'SOLIDWORKS' in win32gui.GetWindowText(hwnd):
                sw_hwnds.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(enum_callback, hwnds)
        hwnd = hwnds[0] if hwnds else None
    
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        print("SW window brought to front")
except ImportError:
    print("win32gui not available, SW should be visible on taskbar")

time.sleep(1)

# Create simple part - just a cylinder
model = sw.ActiveDoc
templates = glob.glob(r"C:\ProgramData\SolidWorks\SOLIDWORKS *\templates\*.prtdot")
sw.NewDocument(templates[0], 0, 0, 0)
time.sleep(2)
model = sw.ActiveDoc
print(f"Doc: {model.GetTitle}")

# Sketch circle
model.ClearSelection2(True)
model.Extension.SelectByID2("前视基准面", "PLANE", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.InsertSketch2(True)
model.SketchManager.CreateCircle(0, 0, 0, 0.025, 0, 0)
model.InsertSketch2(True)

# Select and extrude
model.ClearSelection2(True)
model.Extension.SelectByID2("草图1", "SKETCH", 0, 0, 0, False, 0, VARIANT(pythoncom.VT_DISPATCH, None), 0)
model.FeatureManager.FeatureExtrusion(True, False, False, False, 0.02, False, 0, False, False, False, False, False, False, False, False, 0, 0, False, False, False)
print("Cylinder extruded!")

# Zoom
model.ViewZoomtofit2()

print("\nSW should be visible now with a cylinder!")
print("Check the SW window.")

pythoncom.CoUninitialize()
