---
name: health-data-toolkit
version: 1.0.0
display_name: 食刻账本
display_name_en: Meal Ledger
description_zh: 食刻账本——餐食营养自动记账与体重追踪脚本工具箱。分析零手算、体重幂等记、闭环自动查；配置化可复用。用户报体重、发餐食清单/照片要分析、要查哪几天没记全三餐、要初始化/撤回健康档案时使用。
description_en: Meal Ledger is a parameterized script toolkit for automatic meal nutrition logging and weight tracking. Analysis needs zero manual math, weight logging is idempotent, and meal-gap closure checks run automatically; all data paths and body profiles are config-driven, so it is reusable for any user or machine. Use it when the user reports a body weight, sends a meal list or photo for nutrition analysis, asks which days are missing any of the three meals, or wants to initialize or roll back a health profile.
description: 食刻账本——餐食营养自动记账与体重追踪脚本工具箱。分析零手算、体重幂等记、闭环自动查；配置化可复用。用户报体重、发餐食清单/照片要分析、要查哪几天没记全三餐、要初始化/撤回健康档案时使用。
---
# 食刻账本（health-data-toolkit）

> **一句话简介**：把"吃了什么、掉没掉秤"变成自动记账——AI 识别一秒估，脚本算账零误差，改一份配置就能给任何人记账。

一套参数化脚本资产，负责「计算 + 写入」两个确定性环节；识别、估重、纠错等判断类工作由 AI 完成。数据目录与身体档案全部由配置驱动，**换用户/换机器只需改 config.json**。

## 配置（scripts/config.json）

```json
{
  "data_dir": "<健康档案目录>",          // 存放下面 4 个 xlsx/docx 的目录
  "profile": {                           // 身体档案（可只写需要的字段）
    "height_cm": 166, "start_weight": 82.7, "start_date": "2026-08-10",
    "phase2_target": 77.0, "phase2_deadline": "2026-09-24", "phase2_start": 79.65,
    "protein_floor": 90, "daily_budget": [1400, 1500], "tdee": [2400, 2500]
  }
}
```

- 环境变量覆盖：`HEALTH_DATA_DIR`（临时切换数据目录）、`HEALTH_TOOLKIT_CONFIG`（临时切换配置文件）——测试/多档案时用，不污染正式配置
- BMI 分母默认按 `height_cm` 自动计算
- 首次使用：`python scripts/init_meal_system.py` 幂等生成 4 个档案文件（餐食记录 xlsx/docx + 食物数据库 + 首条示例）
- Python 依赖：openpyxl、python-docx

## 数据目录内的文件

| 文件 | 读写脚本 |
|---|---|
| 餐食营养记录.xlsx（Sheet「餐食记录」） | append / delete / check_closure 读写，analyze 只读 |
| 餐食营养记录.docx | append / delete 追加/删除节 |
| 食物营养数据库.xlsx（Sheet「食物数据库」，13列） | append 追加新食物（同名同单位跳过），analyze 只读 |
| 体重记录.xlsx（Sheet「体重记录」，9列） | record_weight 追加（幂等） |

数据库 13 列：名称、单位、kcal、碳水、蛋白、脂肪、纤维、VA、VB1、VB2、VC、VE、备注。单位格式支持 `100g` / `100ml` / `1个(50g)` / `1根(120g可食)` / `10g` 等（脚本自动解析基准克重）。

## 脚本清单与调用时机

| 脚本 | 什么时候调 | 用法 |
|---|---|---|
| **analyze_meal.py** | 每次餐食分析（阶段一/修正重算），替代手算 | `python analyze_meal.py items.json [--json] [--save out.json]` |
| **record_weight.py** | 用户报体重数字时 | `python record_weight.py 79.4 [--date 2026-09-03] [--note "..."] [--dry-run]` |
| **check_closure.py** | 记录体重或早餐前（补录检查）；复盘统计 | `python check_closure.py [--days 5] [--json]`（有缺口 exit 1） |
| **append_meal.py** | 用户明确说「存入文档/记录下来」后 | `python append_meal.py meal.json` |
| **delete_meal.py** | 用户明确说撤回/删除某餐时 | `python delete_meal.py --date 日期 --meal 餐次 [--index 0]` |
| **init_meal_system.py** | 新用户首次使用 / 档案损坏重建 | `python init_meal_system.py`（幂等） |

### analyze_meal.py 输入格式（items.json）

```json
{
  "date": "2026-09-11", "meal": "早餐",
  "items": [
    {"name": "糙米饭", "grams": 80},
    {"name": "甜面酱", "grams": 10,
     "per100": {"kcal": 130, "carb": 27, "protein": 4, "fat": 0.6, "fiber": 1.2}}
  ]
}
```

- 库内食物按名匹配（先精确后包含，多候选会列出）；库外食物必须带 `per100`
- 输出含逐项换算、合计、供能比（碳水4/蛋白4/脂肪9）与警告；误差统一 ±20% 由调用方标注
- `--save` 直接生成 append_meal.py 兼容 JSON（可再补 note/advice 后入档）

### append_meal.py 输入格式（meal.json）

核心字段：`date, meal, detail, kcal, carb, protein, fat, fiber, va, vb1, vb2, vc, ve, note, advice[]`；可选 `new_foods`（13列行数组，自动入库并打【新增食物】备注）、`photo`（原图路径，自动归档 photos/日期_餐次.jpg）。

### record_weight.py 自动计算

较前日、累计减重（自 start_weight）、BMI、距 phase2_target 剩余、剩余天数、日均需减、第二程进度（自 phase2_start）——同日期重复执行自动跳过（幂等）。

## AI 侧流程约定（与 meal-nutrition-log 技能衔接）

1. 用户报体重 → `check_closure.py` 查昨天闭环 → 有缺口先提醒补录 → `record_weight.py` 入档 → 推送结果
2. 用户发餐食 → AI 识别估重（纠错表/数据库核对）→ `analyze_meal.py` 计算 → 输出分析 → 用户确认后构造 meal.json → `append_meal.py` 入档
3. 用户说撤回 → `delete_meal.py`（自动回滚该餐新增食物）
4. 结果推送等输出类动作不在本工具箱范围内（由会话层处理）
