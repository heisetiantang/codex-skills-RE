# -*- coding: utf-8 -*-
"""_config.py — health-data-toolkit 统一配置加载

配置优先级（高→低）:
  1. 环境变量 HEALTH_DATA_DIR        —— 直接指定数据目录（隔离测试/多档案切换用）
  2. config.json 的 data_dir          —— 正式配置
  3. <脚本目录>/data                  —— 兜底默认（自动创建）

config.json 位置: 环境变量 HEALTH_TOOLKIT_CONFIG 指定完整路径, 或默认脚本目录下 config.json；
没有 config.json 时使用 config.example.json 的默认值。

profile 字段（均可选，缺省用示例值）:
  height_cm / start_weight / start_date / phase2_target / phase2_deadline /
  phase2_start / protein_floor / daily_budget[kcal] / tdee[kcal]
  bmi_denom 默认由 height_cm 自动计算，可显式覆盖。
"""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_raw():
    p = os.environ.get("HEALTH_TOOLKIT_CONFIG") or os.path.join(HERE, "config.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")), p
    ex = os.path.join(HERE, "config.example.json")
    if os.path.exists(ex):
        return json.load(open(ex, encoding="utf-8")), ex + "（未创建 config.json，使用示例默认）"
    return {}, "（无配置文件，使用内置默认）"


_raw, _src = _load_raw()

DATA_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("HEALTH_DATA_DIR") or _raw.get("data_dir") or os.path.join(HERE, "data")))

PROFILE = {
    "height_cm": 166,
    "start_weight": 82.7,
    "start_date": "2026-08-10",
    "phase2_target": 77.0,
    "phase2_deadline": "2026-09-24",
    "phase2_start": 79.65,
    "protein_floor": 90,
    "daily_budget": [1400, 1500],
    "tdee": [2400, 2500],
}
PROFILE.update(_raw.get("profile") or {})
PROFILE.setdefault("bmi_denom", round((PROFILE["height_cm"] / 100) ** 2, 3))

os.makedirs(DATA_DIR, exist_ok=True)

if __name__ == "__main__":
    print(json.dumps({"config_source": _src, "data_dir": DATA_DIR, "profile": PROFILE},
                     ensure_ascii=False, indent=1))
