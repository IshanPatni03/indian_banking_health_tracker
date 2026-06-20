"""
RBI Banking Health Tracker — Python EDA
Connects to MySQL, runs analysis, saves charts to /charts folder.

Run: python eda.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")

from sqlalchemy import create_engine

# ── MySQL Connection ─────────────────────────────────────────────────────────
MYSQL_USER     = "root"
MYSQL_PASSWORD = "Patniishan*2002"   # ← same password as clean_data_mysql.py
MYSQL_HOST     = "localhost"
MYSQL_DB       = "rbi_banking"

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
)

import os
os.makedirs("charts", exist_ok=True)

# ── Style ────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#F9FAFB",
    "axes.facecolor":   "#F9FAFB",
    "axes.grid":        True,
    "grid.color":       "#E5E7EB",
    "grid.linewidth":   0.7,
    "font.family":      "sans-serif",
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

PSB_COLOR  = "#1D4ED8"   # blue
PVT_COLOR  = "#DC2626"   # red
ALL_COLOR  = "#6B7280"   # grey

PSB_LIST = [
    'STATE BANK OF INDIA','BANK OF BARODA','BANK OF INDIA','CANARA BANK',
    'PUNJAB NATIONAL BANK','UNION BANK OF INDIA','INDIAN BANK',
    'CENTRAL BANK OF INDIA','UCO BANK','BANK OF MAHARASHTRA',
    'PUNJAB AND SIND BANK','INDIAN OVERSEAS BANK'
]
PVT_LIST = [
    'HDFC BANK','ICICI BANK','AXIS BANK','KOTAK MAHINDRA BANK',
    'INDUSIND BANK','YES BANK','FEDERAL BANK','IDBI BANK',
    'BANDHAN BANK','RBL BANK','IDFC FIRST BANK'
]


# ── Chart 1: Gross NPA Trend by Bank Group ───────────────────────────────────
print("Chart 1: Gross NPA Trend...")

df = pd.read_sql("""
    SELECT year,
        SUM(CASE WHEN bank_name IN ({psb}) THEN gross_npa_closing ELSE 0 END) / 100000 AS psb,
        SUM(CASE WHEN bank_name IN ({pvt}) THEN gross_npa_closing ELSE 0 END) / 100000 AS pvt,
        SUM(gross_npa_closing) / 100000 AS total
    FROM npa_movement
    WHERE gross_npa_closing IS NOT NULL
    GROUP BY year ORDER BY year
""".format(
    psb=",".join(f"'{b}'" for b in PSB_LIST),
    pvt=",".join(f"'{b}'" for b in PVT_LIST)
), engine)

fig, ax = plt.subplots(figsize=(12, 5))
ax.fill_between(df.year, df.psb,  alpha=0.15, color=PSB_COLOR)
ax.fill_between(df.year, df.pvt,  alpha=0.15, color=PVT_COLOR)
ax.plot(df.year, df.psb,   color=PSB_COLOR, lw=2.5, label="Public Sector Banks", marker="o", ms=4)
ax.plot(df.year, df.pvt,   color=PVT_COLOR, lw=2.5, label="Private Banks",       marker="o", ms=4)
ax.plot(df.year, df.total, color=ALL_COLOR,  lw=1.5, label="All SCBs",            linestyle="--")
ax.axvline(2016, color="#F59E0B", lw=1.5, linestyle=":", alpha=0.8)
ax.text(2016.2, df.total.max()*0.9, "AQR 2016", fontsize=8, color="#92400E")
ax.axvline(2018, color="#10B981", lw=1.5, linestyle=":", alpha=0.8)
ax.text(2018.2, df.total.max()*0.82, "IBC 2018", fontsize=8, color="#065F46")
ax.set_title("Gross NPA Trend: Public vs Private Banks (2005–2025)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("₹ Lakh Crore")
ax.legend(framealpha=0)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
plt.tight_layout()
plt.savefig("charts/chart1_npa_trend.png", dpi=150)
plt.close()
print("  ✓ saved chart1_npa_trend.png")


# ── Chart 2: Write-offs vs Recoveries ───────────────────────────────────────
print("Chart 2: Write-offs vs Recoveries...")

df = pd.read_sql("""
    SELECT year,
        SUM(gross_npa_addition)  / 100000 AS slippages,
        SUM(gross_npa_reduction) / 100000 AS reductions,
        SUM(gross_npa_writeoff)  / 100000 AS writeoffs
    FROM npa_movement
    WHERE year >= 2013
    GROUP BY year ORDER BY year
""", engine)

fig, ax = plt.subplots(figsize=(12, 5))
width = 0.35
x = range(len(df))
bars1 = ax.bar([i - width/2 for i in x], df.slippages, width, label="Fresh Slippages", color="#EF4444", alpha=0.85)
bars2 = ax.bar([i + width/2 for i in x], df.writeoffs,  width, label="Write-offs",      color="#F97316", alpha=0.85)
ax.plot(x, df.reductions, color=PSB_COLOR, lw=2, label="Total Reductions", marker="D", ms=5)
ax.set_xticks(list(x))
ax.set_xticklabels(df.year.astype(int), rotation=45)
ax.set_title("NPA Slippages vs Write-offs vs Recoveries (2013–2025)", fontsize=13, fontweight="bold", pad=12)
ax.set_ylabel("₹ Lakh Crore")
ax.legend(framealpha=0)
plt.tight_layout()
plt.savefig("charts/chart2_writeoffs_vs_recoveries.png", dpi=150)
plt.close()
print("  ✓ saved chart2_writeoffs_vs_recoveries.png")


# ── Chart 3: ROA Trend — PSB vs Private ─────────────────────────────────────
print("Chart 3: ROA Trend...")

df = pd.read_sql("""
    SELECT year,
        AVG(CASE WHEN bank_name IN ({psb}) THEN roa END) AS roa_psb,
        AVG(CASE WHEN bank_name IN ({pvt}) THEN roa END) AS roa_pvt,
        AVG(roa) AS roa_all
    FROM bank_ratios
    WHERE roa BETWEEN -5 AND 5
    GROUP BY year ORDER BY year
""".format(
    psb=",".join(f"'{b}'" for b in PSB_LIST),
    pvt=",".join(f"'{b}'" for b in PVT_LIST)
), engine)

fig, ax = plt.subplots(figsize=(12, 5))
ax.axhline(0, color="#9CA3AF", lw=1)
ax.fill_between(df.year, df.roa_psb, 0,
    where=(df.roa_psb < 0), alpha=0.15, color="#EF4444", label="_nolegend_")
ax.plot(df.year, df.roa_psb, color=PSB_COLOR, lw=2.5, label="PSBs",         marker="o", ms=4)
ax.plot(df.year, df.roa_pvt, color=PVT_COLOR, lw=2.5, label="Private Banks", marker="o", ms=4)
ax.plot(df.year, df.roa_all, color=ALL_COLOR,  lw=1.5, label="All SCBs",     linestyle="--")
ax.set_title("Return on Assets (ROA): PSBs vs Private Banks (2005–2025)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("ROA (%)")
ax.legend(framealpha=0)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
plt.tight_layout()
plt.savefig("charts/chart3_roa_trend.png", dpi=150)
plt.close()
print("  ✓ saved chart3_roa_trend.png")


# ── Chart 4: NIM Comparison ──────────────────────────────────────────────────
print("Chart 4: NIM Trend...")

df = pd.read_sql("""
    SELECT year,
        AVG(CASE WHEN bank_name IN ({psb}) THEN nim END) AS nim_psb,
        AVG(CASE WHEN bank_name IN ({pvt}) THEN nim END) AS nim_pvt,
        AVG(nim) AS nim_all
    FROM bank_ratios
    WHERE nim BETWEEN 0 AND 10
    GROUP BY year ORDER BY year
""".format(
    psb=",".join(f"'{b}'" for b in PSB_LIST),
    pvt=",".join(f"'{b}'" for b in PVT_LIST)
), engine)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df.year, df.nim_psb, color=PSB_COLOR, lw=2.5, label="PSBs",          marker="o", ms=4)
ax.plot(df.year, df.nim_pvt, color=PVT_COLOR, lw=2.5, label="Private Banks",  marker="o", ms=4)
ax.plot(df.year, df.nim_all, color=ALL_COLOR,  lw=1.5, label="All SCBs",      linestyle="--")
ax.set_title("Net Interest Margin (NIM): PSBs vs Private Banks (2005–2025)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("NIM (%)")
ax.legend(framealpha=0)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
plt.tight_layout()
plt.savefig("charts/chart4_nim_trend.png", dpi=150)
plt.close()
print("  ✓ saved chart4_nim_trend.png")


# ── Chart 5: CRAR Distribution (Latest Year) ────────────────────────────────
print("Chart 5: CRAR Distribution...")

df = pd.read_sql("""
    SELECT bank_name, crar_total
    FROM crar
    WHERE year = (SELECT MAX(year) FROM crar)
      AND crar_total BETWEEN 5 AND 30
    ORDER BY crar_total DESC
    LIMIT 25
""", engine)

colors = ["#10B981" if v >= 12 else "#F59E0B" if v >= 9 else "#EF4444"
          for v in df.crar_total]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(df.bank_name, df.crar_total, color=colors, alpha=0.85)
ax.axvline(9,  color="#EF4444", lw=1.5, linestyle="--", label="RBI Minimum (9%)")
ax.axvline(12, color="#10B981", lw=1.5, linestyle="--", label="Well Capitalised (12%)")
ax.set_title("CRAR by Bank — Latest Year", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("CRAR (%)")
ax.legend(framealpha=0)
plt.tight_layout()
plt.savefig("charts/chart5_crar_distribution.png", dpi=150)
plt.close()
print("  ✓ saved chart5_crar_distribution.png")


# ── Chart 6: Sensitive Sector Exposure ──────────────────────────────────────
print("Chart 6: Sensitive Sector Exposure...")

df = pd.read_sql("""
    SELECT year,
        SUM(real_estate_exposure)    / 100000 AS real_estate,
        SUM(capital_market_exposure) / 100000 AS capital_market,
        SUM(commodities_exposure)    / 100000 AS commodities
    FROM sensitive_sectors
    GROUP BY year ORDER BY year
""", engine)

fig, ax = plt.subplots(figsize=(12, 5))
ax.stackplot(df.year,
    df.real_estate, df.capital_market, df.commodities,
    labels=["Real Estate", "Capital Markets", "Commodities"],
    colors=["#3B82F6", "#8B5CF6", "#F59E0B"], alpha=0.8)
ax.set_title("Bank Exposure to Sensitive Sectors (2005–2025)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("₹ Lakh Crore")
ax.legend(loc="upper left", framealpha=0)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
plt.tight_layout()
plt.savefig("charts/chart6_sensitive_sectors.png", dpi=150)
plt.close()
print("  ✓ saved chart6_sensitive_sectors.png")


# ── Summary Stats ────────────────────────────────────────────────────────────
print("\n── Key Findings ──────────────────────────────────────────────────────")

# PSB NPA peak and current
df_npa = pd.read_sql("""
    SELECT year, SUM(gross_npa_closing)/100000 AS npa
    FROM npa_movement WHERE bank_name IN ({})
    GROUP BY year ORDER BY year
""".format(",".join(f"'{b}'" for b in PSB_LIST)), engine)
peak_yr  = df_npa.loc[df_npa.npa.idxmax(), "year"]
peak_val = df_npa.npa.max()
curr_val = df_npa.iloc[-1]["npa"]
print(f"  PSB Gross NPA peaked at ₹{peak_val:.1f}L Cr in {int(peak_yr)}, "
      f"reduced to ₹{curr_val:.1f}L Cr by {int(df_npa.iloc[-1]['year'])}")

# ROA recovery
df_roa = pd.read_sql("""
    SELECT year, AVG(roa) AS roa FROM bank_ratios
    WHERE bank_name IN ({}) AND roa BETWEEN -5 AND 5
    GROUP BY year ORDER BY year
""".format(",".join(f"'{b}'" for b in PSB_LIST)), engine)
min_roa_yr  = df_roa.loc[df_roa.roa.idxmin(), "year"]
min_roa_val = df_roa.roa.min()
curr_roa    = df_roa.iloc[-1]["roa"]
print(f"  PSB ROA bottomed at {min_roa_val:.2f}% in {int(min_roa_yr)}, "
      f"recovered to {curr_roa:.2f}% by {int(df_roa.iloc[-1]['year'])}")

# CRAR
df_crar = pd.read_sql("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN crar_total < 9 THEN 1 ELSE 0 END) as below_min
    FROM crar WHERE year = (SELECT MAX(year) FROM crar)
    AND crar_total > 0
""", engine)
print(f"  CRAR: {df_crar['below_min'][0]} banks below RBI minimum of 9% in latest year")

print("\n✅ All 6 charts saved to /charts folder")
