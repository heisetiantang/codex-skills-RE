"""Offline self-test: exercises the pure logic only.

Touches NO window, NO focus, NO keyboard, NO clipboard - safe to run while the
user is working. Run it after any edit to the scripts:

    .venv/Scripts/python.exe scripts/selftest.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

import wx_auto as wa  # noqa: E402
import wx_send as ws  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(f"[{'ok' if cond else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not cond:
        FAILED.append(name)


# --------------------------------------------------------------------------- #
# config handling
# --------------------------------------------------------------------------- #
cfg = ws.load_config(None)
check("default config has input_box", "input_box" in cfg and "input_xy" in cfg)
check("default require-idle friendly default", cfg["input_leak_min_pixels"] > 0)

with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
    json.dump({"input_xy": [0.5, 0.5], "ui_wait": 3}, f)
    tmp_cfg_path = f.name
cfg2 = ws.load_config(tmp_cfg_path)
check("config override applied", cfg2["input_xy"] == [0.5, 0.5] and cfg2["ui_wait"] == 3)
check("config override keeps defaults", "picker_box" in cfg2)
os.unlink(tmp_cfg_path)

# --------------------------------------------------------------------------- #
# coordinate maths
# --------------------------------------------------------------------------- #
img = Image.new("RGB", (1920, 1200))
x, y = wa.image_to_screen(960, 600, img)
# centre of a 1920x1200 shot must map to the centre of the virtual screen
vscreen_w = wa.user32.GetSystemMetrics(wa.SM_CXVIRTUALSCREEN)
vscreen_h = wa.user32.GetSystemMetrics(wa.SM_CYVIRTUALSCREEN)
check("image_to_screen converts centre", abs(x - vscreen_w / 2) <= 2 and abs(y - vscreen_h / 2) <= 2,
      f"got ({x},{y}) virtual={vscreen_w}x{vscreen_h}")


class _Rect:
    def __init__(self, l, t, r, b):
        self.left, self.top, self.right, self.bottom = l, t, r, b


rect = _Rect(100, 100, 900, 730)

# --------------------------------------------------------------------------- #
# pixel-diff helpers
# --------------------------------------------------------------------------- #
blank = Image.new("RGB", (1920, 1200), (255, 255, 255))
same = ws.region_changed(blank, blank, rect, cfg["input_box"], cfg)
check("region_changed: identical images -> 0", same == 0, f"got {same}")

# paint a black block inside the input-box region of the second image.
# NOTE: region_changed scales window-relative coords by screenshot/screen width,
# so the synthetic paint must use the same scale.
scale = img.width / wa.user32.GetSystemMetrics(0)
changed_img = blank.copy()
bx0 = int((rect.left + 800 * cfg["input_box"][0]) * scale)
by0 = int((rect.top + 630 * cfg["input_box"][1]) * scale)
for px in range(bx0, bx0 + 200):
    for py in range(by0, by0 + 40):
        changed_img.putpixel((px, py), (0, 0, 0))
changed = ws.region_changed(blank, changed_img, rect, cfg["input_box"], cfg)
check("region_changed: painted block detected", changed > 1000, f"got {changed} (scale={scale})")
check("input leak threshold would fire", changed >= cfg["input_leak_min_pixels"])

# a change OUTSIDE the region must not be reported
outside = blank.copy()
for px in range(10, 60):
    for py in range(10, 60):
        outside.putpixel((px, py), (0, 0, 0))
outside_changed = ws.region_changed(blank, outside, rect, cfg["input_box"], cfg)
check("region_changed: outside change ignored", outside_changed == 0, f"got {outside_changed}")

# --------------------------------------------------------------------------- #
# text resolution (no clipboard involved)
# --------------------------------------------------------------------------- #
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
    f.write("第一行\n第二行 ✅\n")
    tmp_msg = f.name
check("resolve_text reads file", ws.resolve_text(tmp_msg, None) == "第一行\n第二行 ✅\n")
os.unlink(tmp_msg)
check("resolve_text converts \\n", ws.resolve_text(None, "a\\nb") == "a\nb")
check("resolve_text keeps real newlines", ws.resolve_text(None, "a\nb") == "a\nb")

# --------------------------------------------------------------------------- #
# idle helper sanity
# --------------------------------------------------------------------------- #
idle = wa.idle_seconds()
check("idle_seconds returns a sane number", 0 <= idle < 60 * 60 * 24, f"got {idle}")

# --------------------------------------------------------------------------- #
print()
if FAILED:
    print(f"{len(FAILED)} check(s) FAILED: {', '.join(FAILED)}")
    sys.exit(1)
print("all offline checks passed (no window, keyboard or clipboard was touched)")
