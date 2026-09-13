"""
Utility (not part of the required deliverable structure) to build a
SQLite DB from the cleaned CSV and sanity-check every query in
sql/analysis.sql executes without error. Also used by the Streamlit
app's SQL Explorer if desired.
"""
import sqlite3
import pandas as pd

DB_PATH = "data/processed/insightflow.db"


def build_db():
    df = pd.read_csv("data/processed/sales_cleaned.csv", parse_dates=["Order_Date"])
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("sales", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Built {DB_PATH} with {len(df):,} rows.")


def check_queries():
    with open("sql/analysis.sql") as f:
        content = f.read()
    # split on ';' but keep it simple — statements separated by blank-line comments
    raw_statements = [s.strip() for s in content.split(";") if s.strip()]
    conn = sqlite3.connect(DB_PATH)
    ok, fail = 0, 0
    for i, stmt in enumerate(raw_statements, 1):
        # strip leading comment lines within statement
        lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
        clean_stmt = "\n".join(lines).strip()
        if not clean_stmt:
            continue
        try:
            conn.execute(clean_stmt).fetchall()
            ok += 1
        except Exception as e:
            fail += 1
            print(f"Query block {i} FAILED: {e}\n{clean_stmt[:200]}")
    conn.close()
    print(f"Checked queries: {ok} ok, {fail} failed")


if __name__ == "__main__":
    build_db()
    check_queries()
