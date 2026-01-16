#!/usr/bin/env python3
"""
定期実行用スクレイピングスクリプト
ハローワークから最新10件の求人情報を取得してCSVに保存
"""
from playwright.sync_api import sync_playwright
import csv
import os
from datetime import datetime
from urllib.parse import urljoin

# 出力先ディレクトリ
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR

# 都道府県コード (24=三重県)
PREFECTURE_CODE = "24"

def text_by_label(card, label):
    """カードから指定ラベルのテキストを取得"""
    try:
        return card.locator(
            f"xpath=.//td[contains(@class,'fb')][contains(normalize-space(),'{label}')]/following-sibling::td//div"
        ).all_inner_texts()
    except:
        return []

def run_scrape():
    """ハローワークから最新10件を取得"""
    jobs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # ヘッドレスモードで実行
        context = browser.new_context(viewport={"width": 1280, "height": 1000})
        page = context.new_page()

        print(f"[{datetime.now()}] スクレイピング開始...")
        
        page.goto("https://www.hellowork.mhlw.go.jp/kensaku/GECA110010.do?action=initDisp&screenId=GECA110010")
        page.check("#ID_ippanCKBox1")
        page.select_option("#ID_tDFK1CmbBox", value=PREFECTURE_CODE)
        page.click("#ID_Btn")
        
        # 職種選択（システムエンジニア）
        page.evaluate("""openShokushuAssist("3","kiboSuruSKSU1Hidden","kiboSuruSKSU1Label");""")
        page.wait_for_timeout(2000)
        popup = context.pages[-1]
        popup.locator('div.i_box:has(i[alt*="技術職"])').focus()
        popup.keyboard.press("Enter")
        popup.check("#ID_skCheck094")
        popup.click("#ID_ok3")
        
        page.click("#ID_searchBtn")
        page.wait_for_selector("table.kyujin")

        tables = page.locator("table.kyujin")
        count = min(tables.count(), 10)  # 最大10件
        base_url = "https://www.hellowork.mhlw.go.jp/kensaku/"

        for i in range(count):
            card = tables.nth(i)
            
            # 日付抽出
            all_text = card.inner_text()
            lines = [line.replace('\t', '').strip() for line in all_text.split('\n') if line.strip()]
            
            reception_date = ""
            expiry_date = ""
            
            for idx, text in enumerate(lines):
                if "受付年月日：" in text:
                    reception_date = text.replace("受付年月日：", "").strip()
                    if not reception_date and idx + 1 < len(lines):
                        reception_date = lines[idx+1]
                if "紹介期限日：" in text:
                    expiry_date = text.replace("紹介期限日：", "").strip()
                    if not expiry_date and idx + 1 < len(lines):
                        expiry_date = lines[idx+1]

            # 職種
            raw_job_category = card.locator("xpath=.//strong[contains(text(),'職種')]/ancestor::tr//div").first.inner_text().strip()
            
            job = {
                "職種": raw_job_category.replace("職種", "").strip(),
                "事業所名": " ".join(text_by_label(card, "事業所名")),
                "就業場所": " ".join(text_by_label(card, "就業場所")),
                "仕事内容": " ".join(text_by_label(card, "仕事の内容")),
                "雇用形態": " ".join(text_by_label(card, "雇用形態")),
                "賃金": " ".join(text_by_label(card, "賃金")),
                "就業時間": " ".join(text_by_label(card, "就業時間")),
                "休日": " ".join(text_by_label(card, "休日")),
                "年齢": " ".join(text_by_label(card, "年齢")),
                "求人番号": " ".join(text_by_label(card, "求人番号")),
                "受付年月日": reception_date,
                "紹介期限日": expiry_date,
            }
            jobs.append(job)
            print(f"  {i+1}件目取得: {job['事業所名']}")
        
        browser.close()
    
    return jobs

def save_to_csv(jobs):
    """求人情報をCSVに保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"hellowork_jobs_{timestamp}.csv")
    
    if not jobs:
        print("取得データなし")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)
    
    print(f"[{datetime.now()}] CSVに保存完了: {filename}")
    print(f"  合計 {len(jobs)} 件")

if __name__ == "__main__":
    print("=" * 50)
    print(f"定期スクレイピング実行: {datetime.now()}")
    print("=" * 50)
    
    try:
        jobs = run_scrape()
        save_to_csv(jobs)
        print("正常終了")
    except Exception as e:
        print(f"エラー発生: {e}")
        raise
