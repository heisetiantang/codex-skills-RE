# -*- coding: utf-8 -*-
"""撤回脚本：删除指定餐次的记录（Excel 行 + Word 节 + 照片 + 回滚该餐新增食物）。
用法:
  python delete_meal.py --date 2026-08-11 --meal 早餐 [--index 0]
--index 默认 0（最新一条）；同一天同一餐多次记录时用 index 指定第几条（0=最新，1=次新...）
"""
import sys, os, re, json, argparse
from openpyxl import load_workbook
from docx import Document
from docx.oxml.ns import qn

BASE = os.path.dirname(os.path.abspath(__file__))
from _config import DATA_DIR, PROFILE
REC_XLSX = os.path.join(DATA_DIR, "餐食营养记录.xlsx")
REC_DOCX = os.path.join(DATA_DIR, "餐食营养记录.docx")
DB_XLSX = os.path.join(DATA_DIR, "食物营养数据库.xlsx")
PHOTO_DIR = os.path.join(DATA_DIR, "photos")


def _para_text(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()


def rollback_foods(food_names):
    if not food_names:
        return 0
    wb = load_workbook(DB_XLSX)
    ws = wb["食物数据库"]
    removed = 0
    for name in food_names:
        for r in range(ws.max_row, 1, -1):
            if str(ws.cell(row=r, column=1).value) == name:
                ws.delete_rows(r)
                removed += 1
                break
    wb.save(DB_XLSX)
    return removed


def delete_xlsx(date, meal, index):
    wb = load_workbook(REC_XLSX)
    ws = wb["餐食记录"]
    matches = []
    for r in range(ws.max_row, 1, -1):
        if str(ws.cell(row=r, column=1).value) == date and str(ws.cell(row=r, column=2).value) == meal:
            matches.append(r)
    if index >= len(matches):
        print(f"ERROR: 未找到 {date} {meal} 第{index + 1}条记录（共{len(matches)}条）")
        return None
    row_num = matches[index]
    note = str(ws.cell(row=row_num, column=ws.max_column).value or "")
    m = re.search(r"【新增食物:([^】]+)】", note)
    new_foods = m.group(1).split(",") if m else []
    ws.delete_rows(row_num)
    wb.save(REC_XLSX)
    print(f"XLSX row {row_num} deleted")
    return new_foods


def delete_docx(date, meal):
    doc = Document(REC_DOCX)
    target = f"{date} {meal}"
    body = doc.element.body
    elements = list(body)
    start = None
    for i, el in enumerate(elements):
        if el.tag == qn("w:p") and _para_text(el) == target:
            start = i
            break
    if start is None:
        print("WARN: Word 中未找到该节标题")
        return
    end = len(elements)
    for j in range(start + 1, len(elements)):
        el = elements[j]
        if el.tag == qn("w:p"):
            pPr = el.find(qn("w:pPr"))
            if pPr is not None and pPr.find(qn("w:pStyle")) is not None \
                    and pPr.find(qn("w:pStyle")).get(qn("w:val")) == "Heading1":
                end = j
                break
    # 保护 Word 节属性（sectPr）与最后段落不删除——它们是文档结构必需元素
    for el in elements[start:end]:
        if el.tag == qn("w:sectPr"):
            continue
        body.remove(el)
    doc.save(REC_DOCX)
    print(f"DOCX section '{target}' deleted")


def delete_photo(date, meal):
    prefix = f"{date}_{meal}"
    removed = 0
    for f in os.listdir(PHOTO_DIR):
        if f.startswith(prefix):  # 匹配 日期_餐次.jpg 及 日期_餐次_2.jpg 等
            os.remove(os.path.join(PHOTO_DIR, f))
            removed += 1
    print(f"PHOTO deleted: {removed} file(s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--meal", required=True)
    ap.add_argument("--index", type=int, default=0)
    args = ap.parse_args()

    new_foods = delete_xlsx(args.date, args.meal, args.index)
    if new_foods is None:
        sys.exit(1)
    delete_docx(args.date, args.meal)
    delete_photo(args.date, args.meal)
    if new_foods:
        n = rollback_foods(new_foods)
        print(f"DB foods rolled back: {n}")
    print("DELETE DONE")
