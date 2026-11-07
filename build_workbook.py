"""Turn github_trending_weekly.csv into a formatted .xlsx workbook plus paste-ready TSVs."""
import csv
import json
import os
from datetime import date, datetime, timezone

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo

CSV_PATH = "github_trending_weekly.csv"
XLSX_PATH = "github_trending_weekly.xlsx"
TSV_PATH = "github_trending_weekly.tsv"
LANG_TSV_PATH = "github_trending_language_summary.tsv"
META_PATH = "github_trending_weekly.meta.json"

rows = list(csv.reader(open(CSV_PATH, encoding="utf-8-sig")))
header, data = rows[0], [r for r in rows[1:] if r and any(v.strip() for v in r)]
n = len(data)

meta = {"collected_at": "", "source": "https://github.com/trending?since=weekly"}
if os.path.exists(META_PATH):
    meta.update(json.load(open(META_PATH, encoding="utf-8")))
else:  # fall back to the moment the CSV was written
    meta["collected_at"] = datetime.fromtimestamp(
        os.path.getmtime(CSV_PATH), timezone.utc
    ).replace(microsecond=0).isoformat()
collected = meta["collected_at"].replace("+00:00", "Z")
source = meta.get("source") or "https://github.com/trending?since=weekly"

# Analysis is always measured against the collection date, not today's clock.
try:
    as_of = datetime.fromisoformat(meta["collected_at"]).date()
except (ValueError, KeyError):
    as_of = date.today()


def as_int(value, default=0):
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


EXTRA_HEADER = [
    "Weekly growth %",
    "Stars per day (this week)",
    "Age (days)",
    "Age (years)",
]

analysis = []
for r in data:
    gained = as_int(r[5])
    total = as_int(r[6])
    before = total - gained  # stars before this week's run
    growth = round(gained / before * 100, 2) if before > 0 else ""
    per_day = round(gained / 7, 1)
    try:
        age_days = (as_of - datetime.strptime(r[11], "%Y-%m-%d").date()).days
        age_years = round(age_days / 365.25, 1)
    except (ValueError, IndexError):
        age_days, age_years = "", ""
    analysis.append([growth, per_day, age_days, age_years])

full_header = header + EXTRA_HEADER
full_rows = [r + a for r, a in zip(data, analysis)]

wb = Workbook()
ws = wb.active
ws.title = "Weekly Trending"

ws.append(full_header)
for r, a in zip(data, analysis):
    ws.append(
        [int(v) if i in (0, 5, 6, 7, 8, 9, 10) and v != "" else v for i, v in enumerate(r)] + a
    )

head_fill = PatternFill("solid", fgColor="1F2937")
head_font = Font(bold=True, color="FFFFFF")
thin = Side(style="thin", color="D1D5DB")
for c in ws[1]:
    c.fill = head_fill
    c.font = head_font
    c.alignment = Alignment(vertical="center", wrap_text=True)
ws.row_dimensions[1].height = 32

widths = {
    "A": 6, "B": 38, "C": 46, "D": 70, "E": 12, "F": 12, "G": 11,
    "H": 9, "I": 14, "J": 10, "K": 11, "L": 11, "M": 11, "N": 11, "O": 34,
    "P": 15, "Q": 20, "R": 10, "S": 10,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    for c in row:
        c.border = Border(bottom=thin)
        c.alignment = Alignment(vertical="top", wrap_text=c.column in (2, 4, 15))
    for idx in (6, 7, 8, 9, 10, 11):
        row[idx - 1].number_format = "#,##0"
    row[15].number_format = '0.00"%"'
    row[16].number_format = "#,##0.0"
    row[17].number_format = "#,##0"
    row[18].number_format = "0.0"
    link = row[2]
    if link.value:
        link.hyperlink = link.value
        link.font = Font(color="0563C1", underline="single")

ws.freeze_panes = "C2"

tab = Table(displayName="TrendingWeek", ref="A1:S%d" % ws.max_row)
tab.tableStyleInfo = TableStyleInfo(
    name="TableStyleLight9", showRowStripes=True, showColumnStripes=False
)
ws.add_table(tab)

top = min(10, n)
chart = BarChart()
chart.type = "bar"
chart.title = "Stars gained this week (top %d)" % top
chart.x_axis.title = "Stars"
chart.height = max(6, 0.9 * top + 3)
chart.width = 20
data_ref = Reference(ws, min_col=6, min_row=1, max_row=top + 1)
cats = Reference(ws, min_col=2, min_row=2, max_row=top + 1)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
chart.legend = None
ws.add_chart(chart, "U2")

# ---- language pivot -------------------------------------------------------
groups = {}
for (r, a) in zip(data, analysis):
    lang = (r[4] or "").strip() or "(none)"
    g = groups.setdefault(
        lang,
        {"repos": 0, "gained": 0, "total": 0, "dl": 0, "growth": [], "top": "", "top_g": -1},
    )
    g["repos"] += 1
    g["gained"] += as_int(r[5])
    g["total"] += as_int(r[6])
    g["dl"] += as_int(r[8])
    if isinstance(a[0], (int, float)):
        g["growth"].append(a[0])
    if as_int(r[5]) > g["top_g"]:
        g["top"], g["top_g"] = r[1], as_int(r[5])

lang_rows = []
for lang, g in sorted(groups.items(), key=lambda kv: kv[1]["gained"], reverse=True):
    avg = round(sum(g["growth"]) / len(g["growth"]), 2) if g["growth"] else ""
    lang_rows.append([lang, g["repos"], g["gained"], g["total"], g["dl"], avg, g["top"]])

lang_header = [
    "Language",
    "Repos",
    "Stars gained this week",
    "Total stars",
    "Release downloads",
    "Avg weekly growth %",
    "Top repo (this week)",
]

ls = wb.create_sheet("By language")
ls.append(lang_header)
for r in lang_rows:
    ls.append(r)
for c in ls[1]:
    c.fill = head_fill
    c.font = head_font
    c.alignment = Alignment(vertical="center", wrap_text=True)
ls.row_dimensions[1].height = 30
for col, w in {"A": 16, "B": 8, "C": 20, "D": 13, "E": 18, "F": 19, "G": 38}.items():
    ls.column_dimensions[col].width = w
for row in ls.iter_rows(min_row=2, max_row=ls.max_row):
    for c in row:
        c.border = Border(bottom=thin)
    for idx in (2, 3, 4):
        row[idx].number_format = "#,##0"
    row[5].number_format = '0.00"%"'
ls.freeze_panes = "A2"

# ---- notes ----------------------------------------------------------------
notes = wb.create_sheet("Notes")
notes_rows = [
    ["GitHub Trending - weekly top projects"],
    ["Collected (UTC)", collected],
    ["Source", source],
    ["Enrichment", "GitHub REST API v3 (repos + releases endpoints)"],
    ["Sorting", "Stars gained this week, highest first"],
    ["Rows", "%d repositories listed on the weekly trending page" % n],
    [
        "Weekly growth %",
        "Stars gained this week divided by the stars the repo had before this week "
        "(total stars - gained). 49% means it grew by half its size in seven days.",
    ],
    [
        "Stars per day (this week)",
        "Stars gained this week / 7. Compare with Age and Total stars to separate "
        "a genuine breakout from a huge repo adding a normal amount.",
    ],
    ["Age (days / years)", "Collection date minus the repo's GitHub 'created' date (365.25 days/year)."],
    [
        "By language sheet",
        "Repos, stars gained, total stars and downloads summed per language, with the "
        "week's strongest repo in each. Blank language is grouped as (none).",
    ],
    [
        "Explanation",
        "GitHub has no site-wide download counter. 'Release downloads' sums the "
        "download_count of every asset across the repository's releases (latest 100 "
        "releases), and is 0 when a repo ships no release assets.",
    ],
    [
        "Caveat",
        "'Stars gained this week' is GitHub's own trending figure; total stars/forks/"
        "issues/watchers are live API values read at collection time.",
    ],
]
for r in notes_rows:
    notes.append(r)
notes["A1"].font = Font(bold=True, size=14)
for r in range(2, len(notes_rows) + 1):
    notes.cell(r, 1).font = Font(bold=True)
notes.column_dimensions["A"].width = 22
notes.column_dimensions["B"].width = 105
for r in range(2, len(notes_rows) + 1):
    notes.cell(r, 2).alignment = Alignment(wrap_text=True, vertical="top")

wb.save(XLSX_PATH)


# ---- paste-ready TSVs -----------------------------------------------------
def write_tsv(path, head, body):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(str(v) for v in head) + "\n")
        for r in body:
            f.write("\t".join(str(v) for v in r) + "\n")


write_tsv(TSV_PATH, full_header, full_rows)
write_tsv(LANG_TSV_PATH, lang_header, lang_rows)

print("saved", XLSX_PATH, n, "data rows,", len(full_header), "cols, collected", collected)
print("saved", TSV_PATH, "and", LANG_TSV_PATH)
for r in full_rows[:3]:
    print("  growth", r[1], r[15], "%", r[16], "st/day", "age", r[17], "d")
for r in lang_rows:
    print("  lang", r)
