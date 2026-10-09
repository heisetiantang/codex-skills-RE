# 食刻账本（health-data-toolkit）

> 把"吃了什么、掉没掉秤"变成自动记账——AI 识别一秒估，脚本算账零误差，改一份配置就能给任何人记账。

餐食营养分析 + 体重追踪的参数化脚本资产。**脚本管计算与写入（确定性环节），AI 管识别/估重/纠错（判断环节）。**

## 目录结构

```
health-data-toolkit/
├── SKILL.md              # 技能说明（触发条件 + 调用约定）
├── README.md             # 本文件
└── scripts/
    ├── _config.py              # 统一配置加载（数据目录 + 身体档案）
    ├── config.json             # 正式配置（每个用户/机器改这里）
    ├── config.example.json     # 配置模板
    ├── init_meal_system.py     # 首次使用：幂等生成档案文件
    ├── analyze_meal.py         # 营养计算引擎（查库换算 + 供能比）
    ├── check_closure.py        # 三餐闭环检查（补录提醒数据源）
    ├── record_weight.py        # 体重记录固化（自动算指标 + 幂等）
    ├── append_meal.py          # 餐食入档（Excel + Word + 新食物入库 + 照片）
    └── delete_meal.py          # 餐食撤回（含新增食物回滚）
```

## 快速开始

```bash
pip install openpyxl python-docx
cd scripts
# 1. 改 config.json：data_dir 指向你的健康档案目录，profile 填身体参数
python init_meal_system.py     # 生成 餐食记录.xlsx/.docx + 食物营养数据库.xlsx
python record_weight.py 79.4   # 记一条体重试试
```

## 配置说明（scripts/config.json）

```json
{
  "data_dir": "C:/path/to/health",
  "profile": {
    "height_cm": 166,
    "start_weight": 82.7,
    "start_date": "2026-08-10",
    "phase2_target": 77.0,
    "phase2_deadline": "2026-09-24",
    "phase2_start": 79.65,
    "protein_floor": 90,
    "daily_budget": [1400, 1500],
    "tdee": [2400, 2500]
  }
}
```

环境变量可临时覆盖（不改配置文件）：
- `HEALTH_DATA_DIR` —— 临时切换数据目录（多档案/测试）
- `HEALTH_TOOLKIT_CONFIG` —— 临时切换配置文件

BMI 分母默认 `height_cm` 自动换算，可在 profile 里用 `bmi_denom` 显式覆盖。所有 profile 字段均可选，缺省用示例值。

## 脚本速查

| 场景 | 命令 |
|---|---|
| 分析一餐 | `python analyze_meal.py items.json [--json] [--save out.json]` |
| 记体重 | `python record_weight.py 79.4 [--date 2026-09-03] [--note "..."] [--dry-run]` |
| 查哪几天没记全 | `python check_closure.py [--days 5] [--json]`（有缺口 exit 1） |
| 存入一餐 | `python append_meal.py meal.json` |
| 撤回一餐 | `python delete_meal.py --date 2026-09-10 --meal 晚餐 [--index 0]` |

输入 JSON 格式详见 SKILL.md。

## 数据文件（data_dir 下）

- `餐食营养记录.xlsx` / `.docx` —— 每餐一行/一节，只追加
- `食物营养数据库.xlsx` —— 13 列（名称/单位/10 项营养/备注），单位支持 `100g`、`1个(50g)`、`1根(120g可食)` 等
- `体重记录.xlsx` —— 9 列，record_weight 自动创建（缺失时）
- `photos/` —— 原图归档（append_meal photo 字段自动复制）

## 设计原则

1. **幂等**：同日期体重重复写入自动跳过；init 重复运行不破坏数据
2. **只追加不覆盖**：餐食/体重记录绝不改历史行
3. **配置与代码分离**：换人、换机器、多档案只动 config.json / 环境变量
4. **可回滚**：delete_meal 撤回时自动回滚该餐新增到数据库的食物
