import sqlite3
import pandas as pd

# =========================
# 1. DB接続
# =========================
conn = sqlite3.connect("hellowork.db")

# =========================
# 2. テーブル一覧
# =========================
df_tables = pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table';",
    conn
)
print("=== tables ===")
print(df_tables)
print()

# =========================
# 3. jobs テーブル
# =========================
df_jobs = pd.read_sql("SELECT * FROM jobs", conn)

print("=== jobs info ===")
print(df_jobs.info())
print()

# =========================
# 4. 前処理（安全）
# =========================

# job_category の整形
df_jobs.loc[:, "job_category"] = (
    df_jobs["job_category"]
    .str.replace("\n新着", "", regex=False)
    .str.strip()
)

# salary → 数値
df_jobs.loc[:, "salary_num"] = (
    df_jobs["salary"]
    .str.replace(",", "", regex=False)
    .str.extract(r"(\d+)")
    .astype(int)
)

# 日付変換
df_jobs.loc[:, "reception_date"] = pd.to_datetime(
    df_jobs["reception_date"], format="%Y年%m月%d日"
)
df_jobs.loc[:, "expiry_date"] = pd.to_datetime(
    df_jobs["expiry_date"], format="%Y年%m月%d日"
)

# =========================
# 5. 分析
# =========================
print("=== 職種別件数 ===")
print(df_jobs["job_category"].value_counts())
print()

print("=== 給与TOP5 ===")
print(
    df_jobs.sort_values("salary_num", ascending=False)[
        ["company_name", "job_category", "salary", "salary_num"]
    ].head(5)
)
print()

# =========================
# 6. my_list テーブル
# =========================
df_list = pd.read_sql("SELECT * FROM my_list", conn)

print("=== my_list info ===")
print(df_list.info())
print()

# =========================
# 7. merge（★修正ポイント）
# =========================
df_fav = pd.merge(
    df_list,
    df_jobs,
    left_on="job_id",
    right_on="id",
    how="inner",
    suffixes=("_list", "_job")
)

print("=== 保存求人一覧（jobs側の最新情報） ===")
print(
    df_fav[
        [
            "company_name_job",
            "job_category_job",
            "work_location_job",
            "salary_job",
        ]
    ]
)
print()

print("=== 保存求人 職種ランキング ===")
print(df_fav["job_category_job"].value_counts())
print()

# =========================
# 8. 出力
# =========================
df_jobs.to_csv("jobs_cleaned.csv", index=False)
df_jobs.to_excel("jobs_cleaned.xlsx", index=False)

print("CSV / Excel 出力完了")

# =========================
# 9. DBクローズ
# =========================
conn.close()

