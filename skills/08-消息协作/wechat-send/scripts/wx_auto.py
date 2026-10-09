"""Low-level helpers for driving the Windows WeChat desktop client (Weixin.exe 4.x).

WeChat 4.x renders its UI with a custom Qt surface, so UI Automation does not
expose child controls. We therefore drive it with keyboard/mouse input, using
the clipboard to deliver CJK text and emoji reliably.
"""

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_ESCAPE = 0x1B
VK_RETURN = 0x0D
VK_A = 0x41
VK_C = 0x43
VK_F = 0x46
VK_V = 0x56
VK_DELETE = 0x2E
VK_DOWN = 0x28

KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
SW_SHOW = 5
SW_MINIMIZE = 6

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

WEIXIN_CLASSES = ("Qt51514QWindowIcon", "Qt51511QWindowIcon")


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


# --------------------------------------------------------------------------- #
# window discovery / activation
# --------------------------------------------------------------------------- #
def _process_image_name(pid: int) -> str:
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value
        return ""
    finally:
        kernel32.CloseHandle(h)


def find_weixin_window():
    """Return (hwnd, rect) of the largest visible Weixin main window."""
    best = []
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        # 注意：微信 4.x 点右上角关闭 = 隐藏到托盘，此时主窗口
        # IsWindowVisible() 为 False，但它仍是有效目标（activate_window()
        # 会用 ShowWindow(SW_SHOW) 把它恢复出来）。所以这里**不能**按可见性过滤，
        # 否则用户在托盘状态下技能会直接报 "main window not found"。
        buf = ctypes.create_unicode_buffer(512)
        user32.GetClassNameW(hwnd, buf, 512)
        if buf.value not in WEIXIN_CLASSES:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        exe = _process_image_name(pid.value).rsplit("\\", 1)[-1].lower()
        if exe != "weixin.exe":
            return True
        r = _RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        area = (r.right - r.left) * (r.bottom - r.top)
        iconic = bool(user32.IsIconic(hwnd))
        # A minimised window reports an off-screen rect (~ -21333); accept it and
        # let activate_window() restore it before we measure anything.
        if iconic or ((r.right - r.left) > 300 and (r.bottom - r.top) > 300):
            best.append((1 if iconic else area, hwnd, r))
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    if not best:
        return None, None
    best.sort(reverse=True, key=lambda t: t[0])
    _, hwnd, r = best[0]
    return hwnd, r


def is_foreground(hwnd) -> bool:
    return user32.GetForegroundWindow() == hwnd


def tap(vk: int, delay: float = 0.05) -> None:
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(delay)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def activate_window(hwnd) -> bool:
    """Bring window to foreground, restoring it if minimised.

    Windows restricts SetForegroundWindow for background processes, so several
    well-known tricks are tried and success is always verified.
    """
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)
    time.sleep(0.3)

    for _ in range(3):
        # Trick 1: a synthetic Alt tap unlocks SetForegroundWindow.
        tap(VK_MENU, 0.03)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        if is_foreground(hwnd) and not user32.IsIconic(hwnd):
            return True

        # Trick 2: minimise then restore, which forces activation.
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        time.sleep(0.35)
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.4)
        if is_foreground(hwnd) and not user32.IsIconic(hwnd):
            return True

        # Trick 3: flash through TOPMOST.
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        time.sleep(0.2)
        user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        time.sleep(0.2)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        if is_foreground(hwnd) and not user32.IsIconic(hwnd):
            return True

    # Last resort: AttachThreadInput.
    fg = user32.GetForegroundWindow()
    tid_target = user32.GetWindowThreadProcessId(hwnd, None)
    tid_fg = user32.GetWindowThreadProcessId(fg, None)
    cur = kernel32.GetCurrentThreadId()
    attached = []
    for tid in (tid_fg, tid_target):
        if tid and user32.AttachThreadInput(cur, tid, True):
            attached.append(tid)
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        for tid in attached:
            user32.AttachThreadInput(cur, tid, False)
    time.sleep(0.4)
    return is_foreground(hwnd) and not user32.IsIconic(hwnd)


def ensure_foreground(hwnd, attempts: int = 3) -> bool:
    """Activate and verify. A minimised window can be 'foreground' while being
    invisible, which would send keystrokes nowhere - so also require restored."""
    for _ in range(attempts):
        if is_foreground(hwnd) and not user32.IsIconic(hwnd):
            return True
        activate_window(hwnd)
        if is_foreground(hwnd) and not user32.IsIconic(hwnd):
            return True
        time.sleep(0.8)
    return False


# --------------------------------------------------------------------------- #
# clipboard
# --------------------------------------------------------------------------- #
def set_clipboard_text(text: str) -> None:
    import win32clipboard

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


# --------------------------------------------------------------------------- #
# input synthesis
# --------------------------------------------------------------------------- #
def combo(*vks, hold: float = 0.06, tail: float = 0.15) -> None:
    for vk in vks:
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(hold)
    for vk in reversed(vks):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.02)
    time.sleep(tail)


def click(x: int, y: int) -> None:
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.12)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
    time.sleep(0.2)


def screenshot(path: str):
    from PIL import ImageGrab

    img = ImageGrab.grab(all_screens=True)
    img.save(path)
    return img


SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79


def image_to_screen(px, py, img):
    """Convert a pixel coordinate in a full-screen screenshot to screen coords."""
    vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    vw = max(1, user32.GetSystemMetrics(SM_CXVIRTUALSCREEN))
    vh = max(1, user32.GetSystemMetrics(SM_CYVIRTUALSCREEN))
    sx = img.width / vw
    sy = img.height / vh
    return int(vx + px / sx), int(vy + py / sy)


# --------------------------------------------------------------------------- #
# user activity awareness (so automation does not fight the human for the mouse)
# --------------------------------------------------------------------------- #
class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def idle_seconds() -> float:
    """Seconds since the last keyboard/mouse input by anyone on this machine."""
    lii = _LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    if not user32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    return max(0.0, (kernel32.GetTickCount() - lii.dwTime) / 1000.0)


def window_state(hwnd) -> dict:
    """Read-only window state, used by the non-intrusive `probe` stage."""
    r = _RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return {
        "hwnd": hwnd,
        "title": None,
        "rect": (r.left, r.top, r.right, r.bottom),
        "size": (r.right - r.left, r.bottom - r.top),
        "minimised": bool(user32.IsIconic(hwnd)),
        "visible": bool(user32.IsWindowVisible(hwnd)),
        "foreground": is_foreground(hwnd),
    }
