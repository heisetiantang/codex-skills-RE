# -*- coding: utf-8 -*-
"""analyze_meal.py — meal-nutrition-log 核心计算引擎
AI 只负责识别与估重（人脑判断部分），所有营养计算由本脚本完成，消除手算误差。

用法:
  python analyze_meal.py <items.json>            # 输出营养汇总（表格文本）
  python analyze_meal.py <items.json> --json     # 额外输出 JSON（机器可读）
  python analyze_meal.py <items.json> --save out.json  # 生成 append_meal.py 兼容的入档 JSON

items.json 结构:
{
  "date": "2026-09-10", "meal": "早餐",
  "items": [
    {"name": "糙米饭", "grams": 80},                      # 库内食物：按名查库自动换算
    {"name": "甜面酱", "grams": 10,                       # 库外食物：自带每100g营养值
     "per100": {"kcal": 130, "carb": 27, "protein": 4, "fat": 0.6, "fiber": 1.2,
                 "va": 0, "vb1": 0.05, "vb2": 0.1, "vc": 0, "ve": 0}}
  ]
}
- 名称匹配规则：先精确匹配，再包含匹配（如"拌豆角"命中"豆角(凉拌)"类条目取第一个）；
  多个命中时脚本会列出候选，建议用 "name": "库内精确名" 重跑。
- 供能比按 碳水4/蛋白4/脂肪9 换算；误差统一 ±20%（由调用方在文案中标注）。
"""
import sys, os, json, re, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
from _config import DATA_DIR, PROFILE
DB_XLSX = os.path.join(DATA_DIR, "食物营养数据库.xlsx")
KEYS = ["kcal", "carb", "protein", "fat", "fiber", "va", "vb1", "vb2", "vc", "ve"]


def unit_basis(unit):
    """从数据库单位串解析基准克重。'100g'->100, '1个(50g)'->50, '100g可食'->100,
    '1个65g'->65, '1根(120g可食)'->120, '10g'->10, '100ml'->100；无克重信息返回 None。"""
    u = str(unit)
    m = re.search(r"\(([\d.]+)\s*(?:g|ml)", u)      # 括号内克重优先
    if m:
        return float(m.group(1))
    m = re.match(r"^([\d.]+)\s*(g|ml)$", u)          # 纯 100g / 10g / 100ml
    if m:
        return float(m.group(1))
    m = re.match(r"^\d+个\s*([\d.]+)\s*g", u)        # '1个65g'
    if m:
        return float(m.group(1))
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def load_db():
    from openpyxl import load_workbook
    ws = load_workbook(DB_XLSX, data_only=True)["食物数据库"]
    db = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[0]:
            continue
        basis = unit_basis(r[1])
        db.append({
            "name": str(r[0]).strip(), "unit": str(r[1]), "basis": basis,
            "note": str(r[12]) if len(r) > 12 and r[12] else "",
            **{k: _num(r[i + 2]) for i, k in enumerate(KEYS)},
        })
    return db


def find_food(db, name):
    """先精确后包含匹配。返回 (条目或None, 候选列表)。"""
    exact = [f for f in db if f["name"] == name]
    if exact:
        return exact[0], []
    cands = [f for f in db if name in f["name"] or f["name"] in name]
    if len(cands) == 1:
        return cands[0], []
    return None, cands


def analyze(spec):
    db = load_db()
    rows, warnings = [], []
    totals = {k: 0.0 for k in KEYS}
    for it in spec.get("items", []):
        name, grams = it["name"].strip(), float(it["grams"])
        src = ""
        if "per100" in it:  # 库外食物，自带每100g值
            per100 = it["per100"]
            basis = 100.0
            food = {"name": name, "per100": True}
            src = "自带值(新食物)"
        else:
            food, cands = find_food(db, name)
            if food is None:
                warnings.append(f"[跳过] '{name}' 未匹配到数据库（候选{len(cands)}个）；"
                                f"库外食物请提供 per100 字段，或换精确名重跑")
                if cands:
                    warnings.append(f"  候选: {', '.join(c['name'] for c in cands[:6])}")
                continue
            name = food["name"]
            if food["basis"] is None:
                warnings.append(f"[跳过] '{name}' 单位'{food['unit']}'无克重基准，请提供 per100")
                continue
            basis = food["basis"]
            per100 = {k: food[k] for k in KEYS}
            src = f"库内(基准{food['unit']})"
            if "grams" in it and "user_grams" not in it:
                pass
        factor = grams / basis
        vals = {k: per100.get(k, 0) * factor for k in KEYS}
        for k in KEYS:
            totals[k] += vals[k]
        rows.append({"name": name, "grams": grams, "src": src,
                     **{k: round(vals[k], 1) for k in KEYS}})
    kcal = totals["kcal"]
    ratios = {"carb": round(totals["carb"] * 4 / kcal * 100) if kcal else 0,
              "protein": round(totals["protein"] * 4 / kcal * 100) if kcal else 0,
              "fat": round(totals["fat"] * 9 / kcal * 100) if kcal else 0}
    result = {"date": spec.get("date"), "meal": spec.get("meal"),
              "items": rows, "totals": {k: round(v, 1) for k, v in totals.items()},
              "ratio": ratios, "warnings": warnings}
    return result


def render(result):
    out = []
    out.append(f"=== {result.get('date','')} {result.get('meal','')} 营养汇总（误差±20%）===")
    out.append(f"{'食物':<24}{'克重':>8}{'kcal':>8}{'碳水':>7}{'蛋白':>7}{'脂肪':>7}{'纤维':>7}  来源")
    for r in result["items"]:
        out.append(f"{r['name']:<24}{r['grams']:>6.0f}g{r['kcal']:>8.0f}{r['carb']:>7.1f}"
                   f"{r['protein']:>7.1f}{r['fat']:>7.1f}{r['fiber']:>7.1f}  {r['src']}")
    t, ra = result["totals"], result["ratio"]
    out.append(f"合计: {t['kcal']:.0f} kcal ｜ 碳水 {t['carb']:.0f}g ｜ 蛋白 {t['protein']:.0f}g ｜ "
               f"脂肪 {t['fat']:.1f}g ｜ 纤维 {t['fiber']:.1f}g")
    out.append(f"供能比: 碳水 {ra['carb']}% / 蛋白 {ra['protein']}% / 脂肪 {ra['fat']}%")
    for w in result["warnings"]:
        out.append("⚠️ " + w)
    return "\n".join(out)


def save_append_json(spec, result, path):
    """生成 append_meal.py 兼容 JSON（维生素等需调用方补齐的字段留默认）。"""
    new_foods = []
    for it in spec.get("items", []):
        if "per100" in it:
            p = it["per100"]
            new_foods.append([it["name"], "100g", p.get("kcal", 0), p.get("carb", 0),
                              p.get("protein", 0), p.get("fat", 0), p.get("fiber", 0),
                              p.get("va", 0), p.get("vb1", 0), p.get("vb2", 0),
                              p.get("vc", 0), p.get("ve", 0), "脚本入库"])
    t = result["totals"]
    payload = {"date": spec.get("date"), "meal": spec.get("meal"),
               "detail": " + ".join(f"{r['name']}{r['grams']:.0f}g" for r in result["items"]),
               "kcal": round(t["kcal"]), "carb": round(t["carb"]), "protein": round(t["protein"]),
               "fat": round(t["fat"], 1), "fiber": round(t["fiber"], 1),
               "va": round(t["va"]), "vb1": round(t["vb1"], 2), "vb2": round(t["vb2"], 2),
               "vc": round(t["vc"]), "ve": round(t["ve"], 1),
               "note": "analyze_meal.py 计算口径", "advice": []}
    if new_foods:
        payload["new_foods"] = new_foods
    json.dump(payload, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("items_json")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--save")
    args = ap.parse_args()
    spec = json.load(open(args.items_json, encoding="utf-8"))
    result = analyze(spec)
    print(render(result))
    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(result, ensure_ascii=False, indent=1))
    if args.save:
        save_append_json(spec, result, args.save)
        print(f"\n✅ 已生成入档 JSON: {args.save}（可再补 advice/note 后交给 append_meal.py）")
