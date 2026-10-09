"""Send a WeChat message to any chat (group or contact) in safe, verifiable stages.

The WeChat desktop client has no public API, so this drives the UI: search the
chat by name, open it, paste the content from the clipboard, and only press
Enter after the caller has verified a screenshot.

NON-INTRUSIVE BY DEFAULT
------------------------
`--stage probe` is read-only: it never moves the focus, never sends a key.
Use it (plus `scripts/selftest.py`, which touches no UI at all) while the user
is working. Every focus-grabbing stage additionally honours:

  --require-idle SEC   wait until the user has been idle for SEC seconds
  --wait-idle-max SEC  give up after this long (exit code 6) instead of
                       yanking the window away from the user

SEARCH NAVIGATION
-----------------
WeChat's search dropdown may highlight a "search the web" row instead of the
chat (typical for 功能 entries like 文件传输助手, or ambiguous names), so
pressing Enter blindly can open a web page. Therefore:

* run `--stage search` first and LOOK at s1_search.png;
* then run prepare with `--click-entry-y <pixel y of the target row>` (best) or
  `--down <N>`; omit both to accept the highlighted first row.

The script also refuses to continue when the query text leaked into the message
input box (i.e. Ctrl+F did not open the search box) - exit code 5, after
clearing the stray text so nothing can be sent by accident.

Stages
------
probe             read-only: window state, idle time, screenshot. No focus change.
search            open search, paste --chat, screenshot s1_search.png, stop.
prepare           like search, then open the chat and paste the message. No send.
prepare-mention   like prepare but builds an @-mention (所有人 by default, or
                  --mention-name) then pastes the payload.
send              press Enter to send whatever sits in the input box.
abort             clear the input box.

Exit codes: 0 ok, 2 environment failure, 3 safety guard tripped,
            4 picker missing, 5 query leaked into the input box,
            6 user busy (idle gate not satisfied).
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_auto as wa  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    # click point inside the message input box, as a fraction of the window rect
    "input_xy": [0.68, 0.82],
    # input-box region (fractions) used to detect leaked query text
    "input_box": [0.35, 0.70, 0.95, 0.92],
    "input_leak_min_pixels": 600,
    # x position (fraction of window width) used when clicking a search result row
    "result_click_x": 0.30,
    # region (fractions) where the @-member picker appears, used for detection
    "picker_box": [0.28, 0.42, 0.58, 0.80],
    "picker_min_changed_pixels": 1500,
    "ui_wait": 1.2,
    "search_wait": 1.6,
}

FOCUS_STAGES = ("search", "prepare", "prepare-mention", "send", "abort")


def load_config(path):
    cfg = dict(DEFAULTS)
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    return cfg


def out_path(outdir, name):
    os.makedirs(outdir, exist_ok=True)
    return os.path.join(outdir, name)


def guard(hwnd, step, outdir):
    if not wa.ensure_foreground(hwnd):
        wa.screenshot(out_path(outdir, f"abort_{step}.png"))
        print(f"ABORT at {step}: WeChat window is not in the foreground")
        sys.exit(3)
    time.sleep(0.3)


def clear_input_box():
    """Empty the message input box (focus must already be inside it)."""
    wa.combo(wa.VK_CONTROL, wa.VK_A)
    time.sleep(0.2)
    wa.tap(wa.VK_DELETE)
    time.sleep(0.4)


def region_changed(img_a, img_b, rect, box, cfg):
    """Count differing pixels inside a window-relative region of two screenshots."""
    from PIL import ImageChops

    left, top, right, bottom = box
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    scale = img_a.width / max(1, wa.user32.GetSystemMetrics(0))
    crop = (
        int((rect.left + w * left) * scale),
        int((rect.top + h * top) * scale),
        int((rect.left + w * right) * scale),
        int((rect.top + h * bottom) * scale),
    )
    a = img_a.crop(crop).convert("RGB")
    b = img_b.crop(crop).convert("RGB")
    return sum(1 for px in ImageChops.difference(a, b).getdata() if sum(px) > 40)


def open_chat(hwnd, chat, outdir, cfg, args, stage_prefix="s2"):
    """Focus search, type the query, verify nothing leaked into the input box,
    then open the chosen result row and focus the message input box."""
    before = wa.screenshot(out_path(outdir, "s0_before_search.png"))

    guard(hwnd, "focus_search", outdir)
    wa.combo(wa.VK_CONTROL, wa.VK_F)
    time.sleep(0.8)
    guard(hwnd, "paste_chat_name", outdir)
    wa.combo(wa.VK_CONTROL, wa.VK_A)  # replace any leftover query
    time.sleep(0.15)
    wa.set_clipboard_text(chat)
    time.sleep(0.2)
    wa.combo(wa.VK_CONTROL, wa.VK_V)
    time.sleep(cfg["search_wait"])
    img = wa.screenshot(out_path(outdir, "s1_search.png"))

    # Safety: if Ctrl+F did not open the search box, the query lands in the
    # message input box of whatever chat is open - clear it and stop.
    leaked = region_changed(before, img, rect, cfg["input_box"], cfg)
    print(f"input-box leak check: {leaked} changed pixels")
    if leaked >= cfg["input_leak_min_pixels"]:
        wa.click(rect.left + int((rect.right - rect.left) * cfg["input_xy"][0]),
                 rect.top + int((rect.bottom - rect.top) * cfg["input_xy"][1]))
        time.sleep(0.3)
        clear_input_box()
        wa.screenshot(out_path(outdir, "s1_query_leaked.png"))
        print("ABORT: search box did not open; the query text was pasted into the "
              "message input box instead. The stray text has been cleared and "
              "nothing was sent. Check that WeChat is not minimised/busy, then retry.")
        sys.exit(5)

    if args.click_entry_y is not None:
        guard(hwnd, "click_result", outdir)
        sx = rect.left + int((rect.right - rect.left) * cfg["result_click_x"])
        sy = wa.image_to_screen(0, args.click_entry_y, img)[1]
        print(f"clicking search result row at screen ({sx},{sy})")
        wa.click(sx, sy)
    else:
        guard(hwnd, "accept_result", outdir)
        for _ in range(args.down):
            wa.tap(wa.VK_DOWN)
            time.sleep(0.12)
        wa.tap(wa.VK_RETURN)

    time.sleep(cfg["ui_wait"] + 0.6)
    wa.screenshot(out_path(outdir, f"{stage_prefix}_opened.png"))


def picker_visible(before_img, after_img, rect, cfg) -> bool:
    """The @-member picker pops up above the input box, so that region changes."""
    changed = region_changed(before_img, after_img, rect, cfg["picker_box"], cfg)
    print(f"picker check: {changed} changed pixels")
    return changed >= cfg["picker_min_changed_pixels"]


def resolve_text(msg_file, text, what="message"):
    if msg_file:
        if not os.path.isfile(msg_file):
            print(f"FAIL: {what} file not found: {msg_file}")
            sys.exit(2)
        with open(msg_file, "r", encoding="utf-8") as f:
            return f.read()
    if text is None:
        print(f"FAIL: neither --message-file nor --text given for {what}")
        sys.exit(2)
    return text.replace("\\n", "\n")


def wait_for_idle(required, budget):
    """Wait until the user has been idle long enough, or give up."""
    if required <= 0:
        return True
    waited = 0
    while True:
        idle = wa.idle_seconds()
        if idle >= required:
            print(f"idle gate ok: user idle for {idle:.1f}s (>= {required}s)")
            return True
        if waited >= budget:
            print(f"BUSY: user still active (idle {idle:.1f}s); waited {waited}s "
                  f"and refused to take over the screen. Nothing was sent.")
            return False
        print(f"user active (idle {idle:.1f}s), waiting for a {required}s idle gap...")
        time.sleep(5)
        waited += 5


def main():
    p = argparse.ArgumentParser(description="Send a WeChat message via UI automation.")
    p.add_argument("--stage", required=True,
                   choices=["probe", "search", "prepare", "prepare-mention", "send", "abort"])
    p.add_argument("--chat", help="群名称或好友备注名，必须能在微信搜索里命中")
    p.add_argument("--group", dest="chat", help="--chat 的旧别名（兼容已有脚本）")
    p.add_argument("--message-file", help="正文文件路径（UTF-8）")
    p.add_argument("--text", help="正文直接传字符串（与 --message-file 二选一），\\n 会转为换行")
    p.add_argument("--mention-file", help="@消息正文文件路径（UTF-8）")
    p.add_argument("--mention-text", help="@消息正文直接传字符串")
    p.add_argument("--mention-name", default="所有人",
                   help="@谁，默认『所有人』；填具体姓名时会先过滤成员列表再回车")
    p.add_argument("--down", type=int, default=0,
                   help="搜索下拉框里先用方向键下移 N 行再回车（默认 0=直接回车首项）")
    p.add_argument("--click-entry-y", type=int, default=None,
                   help="推荐：目标搜索结果行在 s1_search.png 截图里的像素 Y，脚本会精确点击该行")
    p.add_argument("--require-idle", type=float, default=0.0,
                   help="执行前要求用户已空闲多少秒（0=不检查）。避免和用户抢窗口")
    p.add_argument("--wait-idle-max", type=float, default=120.0,
                   help="等待用户空闲的最长秒数，超时则退出码 6（默认 120）")
    p.add_argument("--outdir", required=True, help="截图输出目录")
    p.add_argument("--config", help="可选 JSON 配置，覆盖默认坐标与等待时长")
    args = p.parse_args()

    if args.stage != "probe" and not args.chat:
        print("FAIL: --chat is required for this stage")
        sys.exit(2)

    cfg = load_config(args.config)
    outdir = os.path.abspath(args.outdir)

    hwnd, _ = wa.find_weixin_window()
    if hwnd is None:
        print("FAIL: Weixin.exe main window not found (WeChat not running / logged in?)")
        sys.exit(2)

    # ---- read-only probe: never touches focus ------------------------------- #
    if args.stage == "probe":
        st = wa.window_state(hwnd)
        print(f"wechat window: {st['size'][0]}x{st['size'][1]} "
              f"rect={st['rect']} minimised={st['minimised']} "
              f"visible={st['visible']} foreground={st['foreground']}")
        print(f"user idle: {wa.idle_seconds():.1f}s")
        wa.screenshot(out_path(outdir, "probe.png"))
        print("PROBE done (read-only, no window was activated).")
        sys.exit(0)

    # ---- polite gate for every stage that needs to take over the screen ----- #
    if not wait_for_idle(args.require_idle, args.wait_idle_max):
        sys.exit(6)

    if not wa.ensure_foreground(hwnd):
        print("ABORT: could not bring the WeChat window to the foreground")
        sys.exit(3)
    time.sleep(1.0)

    global rect
    rect = None
    for _ in range(3):
        hwnd, rect = wa.find_weixin_window()
        if rect is not None and (rect.right - rect.left) > 300 and (rect.bottom - rect.top) > 300:
            break
        wa.activate_window(hwnd)
        time.sleep(0.8)
    else:
        print("FAIL: window rect unavailable after activation (still minimised?)")
        sys.exit(2)

    w, h = rect.right - rect.left, rect.bottom - rect.top
    print(f"stage={args.stage} chat={args.chat!r} hwnd={hwnd} "
          f"rect=({rect.left},{rect.top},{rect.right},{rect.bottom}) {w}x{h}")

    # ---- search only: leave the dropdown open for visual inspection ---------- #
    if args.stage == "search":
        type_query_only(hwnd, args.chat, outdir, cfg)
        print("SEARCH typed (not opened). Inspect s1_search.png, pick the target "
              "row, then run prepare/prepare-mention with --click-entry-y or --down.")
        sys.exit(0)

    if args.stage in ("prepare", "prepare-mention"):
        open_chat(hwnd, args.chat, outdir, cfg, args)
        cx = rect.left + int(w * cfg["input_xy"][0])
        cy = rect.top + int(h * cfg["input_xy"][1])
        guard(hwnd, "click_input", outdir)
        wa.click(cx, cy)
        time.sleep(0.4)
        clear_input_box()

    if args.stage == "prepare":
        message = resolve_text(args.message_file, args.text)
        guard(hwnd, "paste_message", outdir)
        wa.set_clipboard_text(message)
        time.sleep(0.3)
        wa.combo(wa.VK_CONTROL, wa.VK_V)
        time.sleep(cfg["ui_wait"])
        wa.screenshot(out_path(outdir, "s3_prepared.png"))
        print("PREPARED (not sent). Verify s3_prepared.png, then run --stage send.")
        sys.exit(0)

    if args.stage == "prepare-mention":
        payload = resolve_text(args.mention_file, args.mention_text, "mention")

        guard(hwnd, "paste_at", outdir)
        base = wa.screenshot(out_path(outdir, "s3a_before_at.png"))
        wa.set_clipboard_text("@")
        time.sleep(0.3)
        wa.combo(wa.VK_CONTROL, wa.VK_V)
        time.sleep(cfg["ui_wait"] + 0.4)
        after = wa.screenshot(out_path(outdir, "s3a_at_pasted.png"))
        if not picker_visible(base, after, rect, cfg):
            clear_input_box()
            wa.screenshot(out_path(outdir, "s3a_picker_missing.png"))
            print("ABORT: @-member picker did not appear (input box cleared, nothing sent)")
            sys.exit(4)

        name = (args.mention_name or "").strip()
        if name and name != "所有人":
            guard(hwnd, "filter_mention", outdir)
            wa.set_clipboard_text(name)
            time.sleep(0.2)
            wa.combo(wa.VK_CONTROL, wa.VK_V)
            time.sleep(cfg["ui_wait"])
            wa.screenshot(out_path(outdir, "s3a_mention_filtered.png"))

        guard(hwnd, "accept_mention", outdir)
        wa.tap(wa.VK_RETURN)
        time.sleep(cfg["ui_wait"])
        wa.screenshot(out_path(outdir, "s3a_mention_selected.png"))

        guard(hwnd, "paste_mention_payload", outdir)
        wa.set_clipboard_text(payload)
        time.sleep(0.3)
        wa.combo(wa.VK_CONTROL, wa.VK_V)
        time.sleep(cfg["ui_wait"])
        wa.screenshot(out_path(outdir, "s3b_prepared.png"))
        print("MENTION PREPARED (not sent). Verify s3b_prepared.png, then run --stage send.")
        sys.exit(0)

    if args.stage == "send":
        guard(hwnd, "send_enter", outdir)
        wa.tap(wa.VK_RETURN)
        time.sleep(cfg["ui_wait"])
        wa.screenshot(out_path(outdir, "s4_sent.png"))
        print("SEND pressed. Verify s4_sent.png shows the message inside the target chat.")
        sys.exit(0)

    if args.stage == "abort":
        guard(hwnd, "abort_clear", outdir)
        clear_input_box()
        wa.screenshot(out_path(outdir, "s5_aborted.png"))
        print("ABORTED: input box cleared.")
        sys.exit(0)


def type_query_only(hwnd, chat, outdir, cfg):
    """Type the query into WeChat search and stop (used by `--stage search`)."""
    before = wa.screenshot(out_path(outdir, "s0_before_search.png"))
    guard(hwnd, "focus_search", outdir)
    wa.combo(wa.VK_CONTROL, wa.VK_F)
    time.sleep(0.8)
    guard(hwnd, "paste_chat_name", outdir)
    wa.combo(wa.VK_CONTROL, wa.VK_A)
    time.sleep(0.15)
    wa.set_clipboard_text(chat)
    time.sleep(0.2)
    wa.combo(wa.VK_CONTROL, wa.VK_V)
    time.sleep(cfg["search_wait"])
    img = wa.screenshot(out_path(outdir, "s1_search.png"))

    leaked = region_changed(before, img, rect, cfg["input_box"], cfg)
    print(f"input-box leak check: {leaked} changed pixels")
    if leaked >= cfg["input_leak_min_pixels"]:
        wa.click(rect.left + int((rect.right - rect.left) * cfg["input_xy"][0]),
                 rect.top + int((rect.bottom - rect.top) * cfg["input_xy"][1]))
        time.sleep(0.3)
        clear_input_box()
        wa.screenshot(out_path(outdir, "s1_query_leaked.png"))
        print("ABORT: search box did not open; the query text went into the message "
              "input box instead and has been cleared. Nothing was sent.")
        sys.exit(5)


if __name__ == "__main__":
    main()
