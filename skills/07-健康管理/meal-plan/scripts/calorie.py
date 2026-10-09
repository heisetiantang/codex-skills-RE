#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""减脂配餐 · 确定性计算（禁止心算）

用法:
  python calorie.py --weight 70 --goal cut
  python calorie.py --weight 70 --goal cut --activity high
  python calorie.py --check --last 70.0 --now 69.2     # 两周速度自检
  python calorie.py --bmi --weight 70 --height 175
"""
import argparse, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ACT = {"low": 25, "mid": 27.5, "high": 30}
GOAL = {"cut": 0.8, "keep": 1.0}

# 掌拳法参考量（克）
PORTION = {
    "protein": "一掌心 = 100–150 g 瘦肉/鱼",
    "carb": "一拳 = 100–150 g 熟主食",
    "veg": "两拳 = 200–300 g 蔬菜",
    "fat": "一拇指 = 10 g 油 或 15 g 坚果",
}


def main():
    p = argparse.ArgumentParser(description="减脂配餐计算器")
    p.add_argument("--weight", type=float, help="体重 kg")
    p.add_argument("--goal", choices=["cut", "keep"], default="cut")
    p.add_argument("--activity", choices=["low", "mid", "high"], default="low",
                   help="low=久坐(默认) mid=中等 high=活动多")
    p.add_argument("--height", type=float, help="身高 cm（算 BMI 用）")
    p.add_argument("--check", action="store_true", help="两周减脂速度自检")
    p.add_argument("--last", type=float, help="两周前体重 kg")
    p.add_argument("--now", type=float, help="当前体重 kg")
    p.add_argument("--bmi", action="store_true", help="只算 BMI")
    a = p.parse_args()

    if a.bmi:
        if not (a.weight and a.height):
            print("需要 --weight 和 --height")
            return 1
        b = a.weight / (a.height / 100) ** 2
        tag = ("偏瘦" if b < 18.5 else "正常" if b < 24 else
               "超重" if b < 28 else "肥胖")
        print(f"BMI = {b:.1f}  ({tag})")
        if b < 18.5:
            print("⚠️ BMI < 18.5，不建议减脂。")
        return 0

    if a.check:
        if not (a.last and a.now):
            print("需要 --last 和 --now")
            return 1
        rate = (a.last - a.now) / a.last * 100
        print(f"两周体重变化: {a.last} → {a.now} kg   周降幅 ≈ {rate/2:.2f}%")
        w = rate / 2
        if w > 1.0:
            print("→ 太快（>1%/周），加 100 kcal。当前吃得太狠，在掉肌肉。")
        elif w >= 0.5:
            print("→ 理想区间（0.5–1%/周），维持不动。")
        elif w > 0:
            print("→ 偏慢（<0.5%/周），减 100 kcal。")
        else:
            print("→ 停滞，走平台期四查：①隐性热量 ②睡眠 ③水肿期 ④消耗量。")
        return 0

    if not a.weight:
        print("需要 --weight")
        return 1

    base = a.weight * ACT[a.activity]
    target = base * GOAL[a.goal]
    protein = a.weight * 1.6
    print(f"=== 配餐目标（体重 {a.weight} kg，活动={a.activity}，目标={a.goal}）===")
    print(f"每日热量目标 : {target:,.0f} kcal")
    print(f"蛋白质目标   : {protein:,.0f} g   （1.6 g/kg，保肌肉核心）")
    print(f"碳水建议     : {target*0.40/4:,.0f} g  （约 40%，优先粗粮）")
    print(f"脂肪建议     : {target*0.30/9:,.0f} g  （约 30%，含烹调油）")
    print()
    print("每餐结构（掌拳法）:")
    for k, v in PORTION.items():
        print(f"  - {v}")
    print()
    print(f"正餐热量上限 : 600–700 kcal/餐")
    print(f"两周后自检   : python calorie.py --check --last <两周前> --now <现在>")
    if target < 1200:
        print()
        print("⚠️ 目标热量低于 1,200 kcal，不推荐执行。请提高活动档位或咨询临床营养师。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
