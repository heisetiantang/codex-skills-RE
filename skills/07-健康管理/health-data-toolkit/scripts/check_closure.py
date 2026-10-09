# -*- coding: utf-8 -*-
"""check_closure.py — 餐食闭环检查（补录提醒数据源）
读餐食营养记录.xlsx，检查最近 N 天（默认5）哪些天缺 早餐/午餐/晚餐。

用法:
  python check_closure.py                 # 检查最近5天
  python check_closure.py --days 10
  python check_closure.py --json          # 输出 JSON（机器可读）

输出约定:
  - 人类可读清单 + JSON；发现缺口时 exit code = 1（供自动化脚本判断），全闭环 = 0
  - 今天正在记录的餐次不算缺（今天只要求已记的餐次完整，缺的餐次归"今天未到"）
"""
import sys, os, json, argparse
from datetime import date, datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
from _config import DATA_DIR, PROFILE
REC_XLSX = os.path.join(DATA_DIR, "餐食营养记录.xlsx")
MEALS = ["早餐", "午餐", "晚餐"]


def recent_days(n):
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(1, n + 1)]  # 不含今天


def check(days=5):
    from openpyxl import load_workbook
    ws = load_workbook(REC_XLSX, data_only=True)["餐食记录"]
    have = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[0]:
            continue
        d = str(r[0])[:10]
        meal = str(r[1]).strip() if r[1] else ""
        have.setdefault(d, set()).add(meal)
    result = []
    for d in recent_days(days):
        missing = [m for m in MEALS if m not in have.get(d, set())]
        if missing:
            result.append({"date": d, "missing": missing,
                           "recorded": sorted(have.get(d, set()))})
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    gaps = check(args.days)
    if args.json:
        print(json.dumps({"unclosed": gaps}, ensure_ascii=False, indent=1))
    else:
        if not gaps:
            print(f"✅ 最近 {args.days} 天三餐全部闭环")
        else:
            print(f"⚠️ 最近 {args.days} 天有 {len(gaps)} 天不闭环：")
            for g in gaps:
                print(f"  {g['date']}  缺：{'、'.join(g['missing'])}"
                      + (f"（已记：{'、'.join(g['recorded'])}）" if g["recorded"] else "（整天无记录）"))
    sys.exit(1 if gaps else 0)
