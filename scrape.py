import sqlite3
import os
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# 重要：もし環境変数に間違ったパスが入っていたら消去する
if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
    del os.environ["PLAYWRIGHT_BROWSERS_PATH"]

DB_NAME = "hellowork.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_category TEXT, company_name TEXT, work_location TEXT,
        job_description TEXT, employment_type TEXT, salary TEXT,
        working_hours TEXT, holidays TEXT, age_limit TEXT,
        job_number TEXT, disclosure_scope TEXT, detail_url TEXT,
        pdf_url TEXT, reception_date TEXT, expiry_date TEXT
    )
    """)
    conn.commit()
    conn.close()

def text_by_label(card, label):
    try:
        return card.locator(
            f"xpath=.//td[contains(@class,'fb')][contains(normalize-space(),'{label}')]/following-sibling::td//div"
        ).all_inner_texts()
    except:
        return []

def run_hellowork():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM jobs")
    conn.commit()

    with sync_playwright() as p:
        # パスを指定せず、Playwrightの標準インストール先を探させる
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = context.new_page()

        # --- 以下、スクレイピング処理 ---
        page.goto("https://www.hellowork.mhlw.go.jp/kensaku/GECA110010.do?action=initDisp&screenId=GECA110010")
        page.check("#ID_ippanCKBox1")
        page.select_option("#ID_tDFK1CmbBox", value="24")
        page.click("#ID_Btn")
        
        page.evaluate("""openShokushuAssist("3","kiboSuruSKSU1Hidden","kiboSuruSKSU1Label");""")
        page.wait_for_timeout(2000)
        
        popup = context.pages[-1]
        popup.locator('div.i_box:has(i[alt*="技術職"])').focus()
        popup.keyboard.press("Enter")
        popup.check("#ID_skCheck094")
        popup.click("#ID_ok3")
        
        page.click("#ID_searchBtn")
        page.wait_for_selector("table.kyujin")

        base_url = "https://www.hellowork.mhlw.go.jp/kensaku/"
        total = 0
        page_no = 1

        while True:
            print(f"--- {page_no}ページ目 ---")
            tables = page.locator("table.kyujin")
            count = tables.count()

            for i in range(count):
                card = tables.nth(i)
                all_text = card.inner_text()
                lines = [l.strip() for l in all_text.split('\n') if l.strip()]
                
                reception_date = ""
                expiry_date = ""
                for idx, text in enumerate(lines):
                    if "受付年月日：" in text: reception_date = text.replace("受付年月日：", "").strip()
                    if "紹介期限日：" in text: expiry_date = text.replace("紹介期限日：", "").strip()

                try:
                    job_cat = card.locator("xpath=.//strong[contains(text(),'職種')]/ancestor::tr//div").first.inner_text().strip()
                except:
                    job_cat = "不明"
                
                job_data = (
                    job_cat.replace("職種", "").strip(),
                    " ".join(text_by_label(card, "事業所名")),
                    " ".join(text_by_label(card, "就業場所")),
                    " ".join(text_by_label(card, "仕事の内容")),
                    " ".join(text_by_label(card, "雇用形態")),
                    " ".join(text_by_label(card, "賃金")),
                    " ".join(text_by_label(card, "就業時間")),
                    " ".join(text_by_label(card, "休日")),
                    " ".join(text_by_label(card, "年齢")),
                    " ".join(text_by_label(card, "求人番号")),
                    " ".join(text_by_label(card, "公開範囲")),
                    urljoin(base_url, card.locator("#ID_dispDetailBtn").get_attribute("href") or ""),
                    urljoin(base_url, card.locator("#ID_kyujinhyoBtn").get_attribute("href") or ""),
                    reception_date,
                    expiry_date
                )

                conn.execute(
                    "INSERT INTO jobs (job_category,company_name,work_location,job_description,employment_type,salary,working_hours,holidays,age_limit,job_number,disclosure_scope,detail_url,pdf_url,reception_date,expiry_date) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    job_data
                )
                total += 1

            conn.commit()
            
            next_btn = page.locator('input[name="fwListNaviBtnNext"]:not([disabled])')
            if next_btn.count() == 0:
                break
            next_btn.last.click()
            page.wait_for_selector("table.kyujin")
            page_no += 1

        conn.close()
        browser.close()

if __name__ == "__main__":
    run_hellowork()