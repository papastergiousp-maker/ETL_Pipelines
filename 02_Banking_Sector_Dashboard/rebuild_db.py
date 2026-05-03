"""
rebuild_db.py
=============
Rebuilds greek_banking_final.db from the three processed CSV files.
Run this script whenever a CSV is updated.

Usage:
    python rebuild_db.py
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "greek_banking_final.db"
CSV_DIR = BASE / "data" / "processed"

def load_csv(filename):
    path = CSV_DIR / filename
    df = pd.read_csv(path)
    print(f"  Loaded {filename}: {len(df)} rows, columns: {list(df.columns)}")
    return df

def rebuild():
    print("=" * 55)
    print("Greek Banking Sector — SQLite DB Rebuild")
    print("=" * 55)

    # Load CSVs
    print("\n[1/3] Loading CSVs...")
    kpis     = load_csv("kpis_final.csv")
    income   = load_csv("income_statement_final.csv")
    balance  = load_csv("balance_sheet_final.csv")

    # Connect / recreate DB
    print(f"\n[2/3] Writing to {DB_PATH}...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("  Deleted old database.")

    conn = sqlite3.connect(DB_PATH)

    # Write tables
    kpis.to_sql("kpis", conn, index=False, if_exists="replace")
    print(f"  Table 'kpis'             → {len(kpis)} rows")

    income.to_sql("income_statement", conn, index=False, if_exists="replace")
    print(f"  Table 'income_statement' → {len(income)} rows")

    balance.to_sql("balance_sheet", conn, index=False, if_exists="replace")
    print(f"  Table 'balance_sheet'    → {len(balance)} rows")

    # Add indexes for performance
    c = conn.cursor()
    c.execute("CREATE INDEX IF NOT EXISTS idx_kpis_bank_year ON kpis(bank, year)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_inc_bank_year  ON income_statement(bank, year)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_bs_bank_year   ON balance_sheet(bank, year)")
    conn.commit()

    # Verify
    print("\n[3/3] Verification queries...")
    checks = [
        ("kpis",             "SELECT COUNT(*) FROM kpis"),
        ("income_statement", "SELECT COUNT(*) FROM income_statement"),
        ("balance_sheet",    "SELECT COUNT(*) FROM balance_sheet"),
        ("Alpha 2022 Due to banks",
         "SELECT value FROM balance_sheet WHERE bank='Alpha Bank' AND year=2022 AND metric='Due to credit institutions'"),
        ("Alpha 2022 Inv sec",
         "SELECT value FROM balance_sheet WHERE bank='Alpha Bank' AND year=2022 AND metric='Investment securities'"),
        ("Sector NII 2024",
         "SELECT ROUND(SUM(nii),1) FROM kpis WHERE year=2024"),
        ("NPE ratio NBG 2024",
         "SELECT npe_ratio FROM kpis WHERE bank='NBG' AND year=2024"),
        ("NPE ratio Alpha 2022",
         "SELECT npe_ratio FROM kpis WHERE bank='Alpha Bank' AND year=2022"),
    ]
    for label, sql in checks:
        row = conn.execute(sql).fetchone()
        print(f"  {label:35s} = {row[0]}")

    conn.close()
    print(f"\n✓  Database rebuilt successfully: {DB_PATH}")
    print("  Open index.html in a browser to verify the dashboard.\n")

if __name__ == "__main__":
    rebuild()
