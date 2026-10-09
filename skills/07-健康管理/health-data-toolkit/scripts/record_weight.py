# -*- coding: utf-8 -*-
"""record_weight.py — 体重记录固化脚本
自动算 较前日/累计减重/进度/BMI/距目标/剩余天数/日均需减，幂等写入体重记录.xlsx（同日期跳过）。

用法:
  python record_weight.py 79.4                       # 记今天
  python record_weight.py 79.4 --date 2026-09-03
  python record_weight.py 79.4 --note "第一程达成"    # 追加备注
  python record_weight.py --dry-run 79.4             # 只算不写

身体参数与目标（用户 2026-08-11 设定，改动请改这里）:
  身高166cm(BMI分母2.756)、起始82.7(8/10)、第一程目标79.5(已达成)、
  第二程目标77.0(截止2026-09-24)、蛋白保底90g/天
"""
import sys, os, json, argparse
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
from _config import DATA_DIR, PROFILE
WB_XLSX = os.path.join(DATA_DIR, "体重记录.xlsx")


def next_checkpoint_note(w):
    """里程碑提示（中检规则 2026-09-10 固化）。"""
    p = PROFILE
    bmi = w / p["bmi_denom"]
    return bmi


def ensure_wb():
    """体重记录.xlsx 不存在时自动创建（幂等，含表头）。"""
    if os.path.exists(WB_XLSX):
        return
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "体重记录"
    ws.append(("日期", "体重(kg)", "较前日", "累计减重", "目标进度",
               "距目标(kg)", "剩余天数", "日均需减", "备注"))
    wb.save(WB_XLSX)


def compute(weight, dstr):
    from openpyxl import load_workbook
    ensure_wb()
    ws = load_workbook(WB_XLSX, data_only=True)["体重记录"]
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]
    prev = rows[-1] if rows else None
    p = PROFILE
    delta = round(weight - prev[1], 2) if prev else None
    cum = round(p["start_weight"] - weight, 2)
    bmi = round(weight / p["bmi_denom"], 2)
    to_goal = round(weight - p["phase2_target"], 2)
    dl = datetime.strptime(p["phase2_deadline"], "%Y-%m-%d").date()
    d = datetime.strptime(dstr, "%Y-%m-%d").date()
    days_left = max((dl - d).days, 0)
    per_day = round(to_goal / days_left, 3) if days_left > 0 and to_goal > 0 else 0.0
    # 第二程进度：从 79.65 起算
    total = p["phase2_start"] - p["phase2_target"]
    done = p["phase2_start"] - weight
    progress = f"{done/total*100:.0f}%" if done > 0 else "-"
    return {"date": dstr, "weight": weight, "delta": delta, "cum": cum,
            "bmi": bmi, "to_goal": to_goal, "days_left": days_left,
            "per_day": per_day, "progress": progress,
            "prev_date": str(prev[0])[:10] if prev else None, "prev_weight": prev[1] if prev else None}


def write(res, note):
    from openpyxl import load_workbook
    wb = load_workbook(WB_XLSX)
    ws = wb["体重记录"]
    existing = [str(r[0])[:10] for r in ws.iter_rows(min_row=2, values_only=True)]
    if res["date"] in existing:
        return False
    head = (f"较{res['prev_date']}{res['delta']:+}" if res["prev_date"] is not None else "首条记录")
    auto = (f"{head}；累计{res['cum']}；"
            f"第二程进度{res['progress']}；距{PROFILE['phase2_target']}剩{res['to_goal']}kg/{res['days_left']}天"
            f"（日均{res['per_day']}）；BMI {res['bmi']}")
    ws.append((res["date"], res["weight"], res["delta"], res["cum"],
               res["progress"], res["to_goal"], res["days_left"],
               res["per_day"] if res["per_day"] else "-", f"{auto}；{note}" if note else auto))
    wb.save(WB_XLSX)
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("weight", type=float)
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--note", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    res = compute(args.weight, args.date)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if args.dry_run:
        print("（dry-run，未写入）")
    else:
        ok = write(res, args.note)
        print(f"✅ 已写入 {res['date']} {res['weight']}kg" if ok
              else f"⏭️ {res['date']} 已有记录，跳过（幂等）")
