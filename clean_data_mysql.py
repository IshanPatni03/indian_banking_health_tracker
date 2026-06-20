"""
RBI Banking Data Cleaner - MySQL Version
Cleans all 7 RBI tables and loads them into MySQL (rbi_banking database).

SETUP:
1. Create database in MySQL Workbench: CREATE DATABASE rbi_banking;
2. Fill in your MySQL password below where it says YOUR_PASSWORD_HERE
3. Put this script in the same folder as your 7 RBI Excel files
4. Run: python clean_data_mysql.py
"""

import pandas as pd
import openpyxl
from datetime import datetime
from sqlalchemy import create_engine, text

# ── MySQL Connection ─────────────────────────────────────────────────────────
MYSQL_USER     = "root"
MYSQL_PASSWORD = "Patniishan*2002"   # ← replace with your MySQL password
MYSQL_HOST     = "localhost"
MYSQL_DB       = "rbi_banking"

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}",
    echo=False
)

def to_mysql(df, table_name):
    df.to_sql(table_name, engine, if_exists="replace", index=False)

# ── File Paths (put Excel files in same folder as this script) ───────────────
FILES = {
    "npa":       "table6_npa.xlsx",
    "ratios":    "table11_bank_ratios.xlsx",
    "group":     "table10_group_ratios.xlsx",
    "sensitive": "table8_sensitive_sectors.xlsx",
    "assets":    "table1_assets_liabilities.xlsx",
    "earnings":  "table2_earnings_expenses.xlsx",
    "crar":      "table3_crar.xlsx",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
import re

def fix_year(val):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except: pass
    if isinstance(val, datetime):
        return val.year
    if isinstance(val, (int, float)):
        if val > 3000:
            return datetime.fromordinal(datetime(1900,1,1).toordinal() + int(val) - 2).year
        if 2000 <= val <= 2100:
            return int(val)
        return None
    if isinstance(val, str):
        val = val.strip()
        m = re.match(r'^(20\d\d)-(\d{2})\s*$', val)
        if m: return int("20" + m.group(2))
        m2 = re.match(r'^(20\d\d)$', val)
        if m2: return int(m2.group(1))
    return None

def clean_numeric(val):
    if val in ["-", "–", None, ""]: return None
    try: return float(val)
    except: return None

def read_wb(filename):
    return openpyxl.load_workbook(filename, read_only=True, data_only=True)

BANK_GROUPS = {
    "PUBLIC SECTOR BANKS", "PRIVATE SECTOR BANKS", "FOREIGN BANKS",
    "SMALL FINANCE BANKS", "PAYMENTS BANKS", "ALL SCHEDULED COMMERCIAL BANKS",
    "ALL SCHEDULED COMMERICIAL BANKS", "NATIONALISED BANKS",
    "STATE BANK OF INDIA AND ITS ASSOCIATES"
}
def is_group(name):
    return name is None or str(name).strip().upper() in BANK_GROUPS


# ── TABLE 6: NPA Movement ────────────────────────────────────────────────────
print("Cleaning Table 6: NPA Movement...")
wb = read_wb(FILES["npa"])
rows = list(wb.active.iter_rows(values_only=True))
records, current_year = [], None
for row in rows:
    yv, bv = row[1], row[2]
    if yv is not None and bv is None:
        current_year = fix_year(yv); continue
    if yv is not None and bv is not None:
        current_year = fix_year(yv)
    if bv is None or current_year is None: continue
    bank = str(bv).strip()
    if is_group(bank) or len(bank) < 2: continue
    try:
        records.append({"year": current_year, "bank_name": bank,
            "gross_npa_opening": clean_numeric(row[3]),
            "gross_npa_addition": clean_numeric(row[4]),
            "gross_npa_reduction": clean_numeric(row[5]),
            "gross_npa_writeoff": clean_numeric(row[6]),
            "gross_npa_closing": clean_numeric(row[7]),
            "net_npa_opening": clean_numeric(row[8]),
            "net_npa_closing": clean_numeric(row[9]),
        })
    except IndexError: continue
df = pd.DataFrame(records).dropna(subset=["gross_npa_closing"])
to_mysql(df, "npa_movement")
print(f"  ✓ npa_movement: {len(df)} rows, {df['year'].min()}–{df['year'].max()}")


# ── TABLE 11: Bank-wise Ratios ───────────────────────────────────────────────
print("Cleaning Table 11: Bank-wise Ratios...")
wb = read_wb(FILES["ratios"])
rows = list(wb.active.iter_rows(values_only=True))
records, current_year = [], None
for row in rows[7:]:
    yv, bv = row[1], row[2]
    if yv is not None: current_year = fix_year(yv)
    if bv is None or current_year is None: continue
    bank = str(bv).strip()
    if is_group(bank) or len(bank) < 2: continue
    try:
        records.append({"year": current_year, "bank_name": bank,
            "cash_deposit_ratio":       clean_numeric(row[3]),
            "credit_deposit_ratio":     clean_numeric(row[4]),
            "investment_deposit_ratio": clean_numeric(row[5]),
            "nim":                      clean_numeric(row[14]),
            "roa":                      clean_numeric(row[23]),
            "roe":                      clean_numeric(row[24]),
            "cost_of_deposits":         clean_numeric(row[25]),
            "cost_of_funds":            clean_numeric(row[27]),
            "return_on_advances":       clean_numeric(row[28]),
            "business_per_employee":    clean_numeric(row[32]),
            "profit_per_employee":      clean_numeric(row[33]),
            "crar_total":               clean_numeric(row[34]),
            "crar_tier1":               clean_numeric(row[35]),
            "crar_tier2":               clean_numeric(row[36]),
        })
    except IndexError: continue
df = pd.DataFrame(records).dropna(subset=["credit_deposit_ratio"])
to_mysql(df, "bank_ratios")
print(f"  ✓ bank_ratios: {len(df)} rows, {df['year'].min()}–{df['year'].max()}")


# ── TABLE 10: Bank Group Ratios ──────────────────────────────────────────────
print("Cleaning Table 10: Group Ratios...")
wb = read_wb(FILES["group"])
rows = list(wb.active.iter_rows(values_only=True))
KEY_RATIOS = {
    "1.": "cash_deposit_ratio", "2.": "credit_deposit_ratio",
    "3.": "investment_deposit_ratio", "12.": "nim",
    "21.": "roa", "22.": "roe", "23.": "cost_of_deposits",
    "32.": "crar_total", "33.": "crar_tier1", "34.": "crar_tier2",
}
def get_ratio_key(v):
    m = re.match(r'^\s*(\d+)\.', str(v))
    return m.group(1) + "." if m else None

records, current_year, current_data = [], None, {}
def flush(yr, data):
    if yr and data:
        records.append({"year": yr, **data})

for row in rows[7:]:
    yv, rv = row[2], row[3]
    if yv is not None and str(yv).strip() not in ["Year","Ratios",""]:
        flush(current_year, current_data)
        current_year = fix_year(str(yv).strip())
        current_data = {}
    if rv is None or current_year is None: continue
    rkey = get_ratio_key(rv)
    if rkey and rkey in KEY_RATIOS:
        cn = KEY_RATIOS[rkey]
        try:
            current_data[cn+"_psb"]     = clean_numeric(row[6])
            current_data[cn+"_pvt"]     = clean_numeric(row[7])
            current_data[cn+"_foreign"] = clean_numeric(row[8])
            current_data[cn+"_sfb"]     = clean_numeric(row[9])
            current_data[cn+"_all"]     = clean_numeric(row[11])
        except IndexError: pass
flush(current_year, current_data)
df = pd.DataFrame(records).dropna(subset=["year"])
to_mysql(df, "group_ratios")
print(f"  ✓ group_ratios: {len(df)} rows, {df['year'].min()}–{df['year'].max()}")


# ── TABLE 8: Sensitive Sectors ───────────────────────────────────────────────
print("Cleaning Table 8: Sensitive Sectors...")
wb = read_wb(FILES["sensitive"])
rows = list(wb.active.iter_rows(values_only=True))
records, current_year = [], None
for row in rows:
    yv, bv = row[1], row[2]
    if yv is not None and isinstance(yv, (int, float)):
        current_year = fix_year(yv)
    elif yv is not None and str(yv).strip() not in ["Year","","None"]:
        current_year = fix_year(str(yv))
    if bv is None or current_year is None: continue
    bank = str(bv).strip()
    if is_group(bank) or len(bank) < 2: continue
    try:
        records.append({"year": current_year, "bank_name": bank,
            "capital_market_exposure":  clean_numeric(row[3]),
            "real_estate_exposure":     clean_numeric(row[4]),
            "commodities_exposure":     clean_numeric(row[5]),
            "total_sensitive_exposure": clean_numeric(row[6]),
        })
    except IndexError: continue
df = pd.DataFrame(records).dropna(subset=["total_sensitive_exposure"])
to_mysql(df, "sensitive_sectors")
print(f"  ✓ sensitive_sectors: {len(df)} rows")


# ── TABLE 1: Assets ──────────────────────────────────────────────────────────
print("Cleaning Table 1: Assets...")
wb = read_wb(FILES["assets"])
ws = wb["ASSETS"]
rows = list(ws.iter_rows(values_only=True))
records, current_year = [], None
for row in rows:
    yv, bv = row[1], row[2]
    if yv is not None and isinstance(yv, (int, float)):
        current_year = fix_year(yv)
    if bv is None or current_year is None: continue
    bank = str(bv).strip()
    if is_group(bank) or len(bank) < 2: continue
    try:
        records.append({"year": current_year, "bank_name": bank,
            "total_advances": clean_numeric(row[20]),
            "investments":    clean_numeric(row[8]),
            "total_assets":   clean_numeric(row[-1]),
        })
    except IndexError: continue
df = pd.DataFrame(records).dropna(subset=["total_advances"])
to_mysql(df, "assets")
print(f"  ✓ assets: {len(df)} rows, {df['year'].min()}–{df['year'].max()}")


# ── TABLE 2: Earnings ────────────────────────────────────────────────────────
print("Cleaning Table 2: Earnings...")
wb = read_wb(FILES["earnings"])
rows = list(wb.active.iter_rows(values_only=True))
records, current_year = [], None
for row in rows[8:]:
    yv, bv = row[1], row[2]
    if yv is not None and isinstance(yv,(int,float)) and 2000<=yv<=2100:
        current_year = int(yv)
    if bv is None or current_year is None: continue
    bank = str(bv).strip()
    if is_group(bank) or len(bank) < 2: continue
    try:
        ti = clean_numeric(row[7])
        to_ = clean_numeric(row[14])
        records.append({"year": current_year, "bank_name": bank,
            "interest_on_advances":  clean_numeric(row[3]),
            "income_on_investments": clean_numeric(row[4]),
            "total_interest_earned": ti,
            "total_other_income":    to_,
            "total_income": (ti or 0)+(to_ or 0) if (ti or to_) else None,
        })
    except IndexError: continue
df = pd.DataFrame(records).dropna(subset=["total_interest_earned"])
to_mysql(df, "earnings")
print(f"  ✓ earnings: {len(df)} rows, {df['year'].min()}–{df['year'].max()}")


# ── TABLE 3: CRAR ────────────────────────────────────────────────────────────
print("Cleaning Table 3: CRAR...")
wb = read_wb(FILES["crar"])
rows = list(wb.active.iter_rows(values_only=True))
records, current_year = [], None
for row in rows[9:]:
    yv, bv = row[1], row[2]
    if yv is not None: current_year = fix_year(yv)
    if bv is None or current_year is None: continue
    bank = str(bv).strip()
    if is_group(bank) or len(bank) < 2: continue
    try:
        t1 = clean_numeric(row[9])
        t2 = clean_numeric(row[10])
        records.append({"year": current_year, "bank_name": bank,
            "basel3_tier1": t1,
            "basel3_tier2": t2,
            "crar_total": round(t1+t2,2) if (t1 and t2) else None,
        })
    except IndexError: continue
df = pd.DataFrame(records).dropna(subset=["basel3_tier1"])
to_mysql(df, "crar")
print(f"  ✓ crar: {len(df)} rows, {df['year'].min()}–{df['year'].max()}")


# ── Summary ──────────────────────────────────────────────────────────────────
print("\n✅ All tables loaded into MySQL database: rbi_banking")
with engine.connect() as c:
    for t in ["npa_movement","bank_ratios","group_ratios","sensitive_sectors","assets","earnings","crar"]:
        n = c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"  {t}: {n} rows")
