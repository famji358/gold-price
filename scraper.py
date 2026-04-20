import json
import re
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
from playwright.sync_api import sync_playwright
import gspread
from google.oauth2.service_account import Credentials

# ================================
# 設定
# ================================
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")

def clean_price(text):
    """テキストから金の1g価格として妥当な数字を取り出す"""
    nums = re.findall(r'[\d,]+', text)
    for n in nums:
        val = int(n.replace(',', ''))
        if 10000 <= val <= 100000:
            return val
    return None

def scrape_all(page):
    """全社の価格を取得"""
    results = {}

    # ================================
    # 田中貴金属（ベンチマーク）
    # ================================
    try:
        page.goto("https://gold.tanaka.co.jp/silver_price/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".price_num", timeout=15000)
        els = page.query_selector_all(".price_num")
        for el in els:
            parent = el.evaluate("el => el.parentElement.className")
            if "price_sell" not in parent:
                price = clean_price(el.inner_text())
                if price:
                    results["田中貴金属"] = price
                    break
        print(f"田中貴金属: {results.get('田中貴金属', '取得失敗')}")
    except Exception as e:
        print(f"田中貴金属エラー: {e}")
        results["田中貴金属"] = None

    # ================================
    # まねきや
    # ================================
    try:
        page.goto("https://manekiya.shop/rate", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_selector("p.price.ingot_price", timeout=20000)
        el = page.query_selector("p.price.ingot_price")
        if el:
            results["まねきや"] = clean_price(el.inner_text())
        print(f"まねきや: {results.get('まねきや', '取得失敗')}")
    except Exception as e:
        print(f"まねきやエラー: {e}")
        results["まねきや"] = None

    # ================================
    # おたからや
    # ================================
    try:
        page.goto("https://www.otakaraya.jp/gold/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".rate-price", timeout=15000)
        el = page.query_selector(".rate-price")
        if el:
            results["おたからや"] = clean_price(el.inner_text())
        print(f"おたからや: {results.get('おたからや', '取得失敗')}")
    except Exception as e:
        print(f"おたからやエラー: {e}")
        results["おたからや"] = None

    # ================================
    # 買取大吉
    # ================================
    try:
        page.goto("https://daikichi-kaitori.jp/gold/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#bold_bm2025", timeout=15000)
        el = page.query_selector("#bold_bm2025")
        if el:
            results["買取大吉"] = clean_price(el.inner_text())
        print(f"買取大吉: {results.get('買取大吉', '取得失敗')}")
    except Exception as e:
        print(f"買取大吉エラー: {e}")
        results["買取大吉"] = None

    # ================================
    # なんぼや
    # ================================
    try:
        page.goto("https://nanboya.com/gold-kaitori/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("span.tp-gold-price.price_number", timeout=15000)
        el = page.query_selector("span.tp-gold-price.price_number")
        if el:
            results["なんぼや"] = clean_price(el.inner_text())
        print(f"なんぼや: {results.get('なんぼや', '取得失敗')}")
    except Exception as e:
        print(f"なんぼやエラー: {e}")
        results["なんぼや"] = None

    # ================================
    # バイセル
    # ================================
    try:
        page.goto("https://buysell-kaitori.com/lp/al/ad-store/lisg/aga/sem/gopla/001_0002.html", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector(".price-value", timeout=10000)
        el = page.query_selector(".price-value")
        if el:
            results["バイセル"] = clean_price(el.inner_text())
        print(f"バイセル: {results.get('バイセル', '取得失敗')}")
    except Exception as e:
        print(f"バイセルエラー: {e}")
        results["バイセル"] = None

    # ================================
    # ブラリバ
    # ================================
    try:
        page.goto("https://brandrevalue.com/cat/gold/ingot", wait_until="domcontentloaded", timeout=60000)
        el = page.query_selector(".metal-price-today")
        if el:
            results["ブラリバ"] = clean_price(el.inner_text())
        print(f"ブラリバ: {results.get('ブラリバ', '取得失敗')}")
    except Exception as e:
        print(f"ブラリバエラー: {e}")
        results["ブラリバ"] = None

    return results

def save_to_spreadsheet(prices, date_str):
    """Googleスプレッドシートに1行追記する"""
    if not SPREADSHEET_ID or not GOOGLE_CREDENTIALS_JSON:
        print("スプレッドシートの設定がないためスキップします")
        return

    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1

        existing = sheet.get_all_values()
        if not existing:
            headers = ["日付", "田中貴金属", "まねきや", "おたからや", "買取大吉", "なんぼや", "バイセル", "ブラリバ"]
            sheet.append_row(headers)

        row = [
            date_str,
            prices.get("田中貴金属", ""),
            prices.get("まねきや", ""),
            prices.get("おたからや", ""),
            prices.get("買取大吉", ""),
            prices.get("なんぼや", ""),
            prices.get("バイセル", ""),
            prices.get("ブラリバ", ""),
        ]
        sheet.append_row(row)
        print(f"スプレッドシートに記録しました: {row}")

    except Exception as e:
        print(f"スプレッドシートへの記録エラー: {e}")

def save_to_json(prices, updated_at):
    """gold_prices.jsonを更新する"""

    kaitori = {k: v for k, v in prices.items() if k != "田中貴金属" and v}
    max_price = max(kaitori.values()) if kaitori else 0

    entries = [
        {
            "name": "田中貴金属",
            "label": "ベンチマーク（公式相場）",
            "url": "https://gold.tanaka.co.jp/silver_price/",
            "affiliate_url": "",
            "price": prices.get("田中貴金属"),
            "is_benchmark": True
        },
        {
            "name": "まねきや",
            "label": "",
            "url": "https://manekiya.shop/rate",
            "affiliate_url": "https://kaitoriranking.net/url/KIN/MANEKIYA-kin/?hikaku=market-rate",
            "price": prices.get("まねきや"),
            "is_benchmark": False
        },
        {
            "name": "おたからや",
            "label": "",
            "url": "https://lp.otakaraya.jp/lp-gold-b/",
            "affiliate_url": "https://kaitoriranking.net/url/KIN/OTAKARAYA-kin/?hikaku=market-rate",
            "price": prices.get("おたからや"),
            "is_benchmark": False
        },
        {
            "name": "買取大吉",
            "label": "",
            "url": "https://daikichi-kaitori.jp/gold/",
            "affiliate_url": "https://kaitoriranking.net/url/KIN/DAIKICHI-kin/?hikaku=market-rate",
            "price": prices.get("買取大吉"),
            "is_benchmark": False
        },
        {
            "name": "なんぼや",
            "label": "",
            "url": "https://nanboya.com/gold-kaitori/",
            "affiliate_url": "https://kaitoriranking.net/url/KIN/NANBOYA-kin/?hikaku=market-rate",
            "price": prices.get("なんぼや"),
            "is_benchmark": False
        },
        {
            "name": "バイセル",
            "label": "",
            "url": "https://buysell-kaitori.com/lp/al/ad-store/lisg/aga/sem/gopla/001_0002.html",
            "affiliate_url": "https://kaitoriranking.net/url/KIN/BUYSELL-kin/?hikaku=market-rate",
            "price": prices.get("バイセル"),
            "is_benchmark": False
        },
        {
            "name": "ブラリバ",
            "label": "",
            "url": "https://brandrevalue.com/recommend/gold",
            "affiliate_url": "https://kaitoriranking.net/url/KIN/BRAREVA-kin/?hikaku=market-rate",
            "price": prices.get("ブラリバ"),
            "is_benchmark": False
        },
    ]

    PRIORITY = ["おたからや", "まねきや", "買取大吉", "ブラリバ", "なんぼや", "バイセル"]

    benchmark = [e for e in entries if e["is_benchmark"]]
    others = [e for e in entries if not e["is_benchmark"]]
    others_sorted = sorted(
        others,
        key=lambda x: (
            -(x["price"] if x["price"] else 0),
            PRIORITY.index(x["name"]) if x["name"] in PRIORITY else 999
        )
    )

    data = {
        "updated_at": updated_at,
        "prices": benchmark + others_sorted
    }

    with open("gold_prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("gold_prices.json を更新しました")

def main():
    now = datetime.now(JST)
    updated_at = now.strftime("%Y年%m月%d日 %H:%M")
    date_str = now.strftime("%Y/%m/%d")

    print("=== 価格取得開始 ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        prices = scrape_all(page)
        browser.close()

    print("\n=== 取得結果 ===")
    for name, price in prices.items():
        print(f"  {name}: {f'{price:,}円/g' if price else '取得失敗'}")

    save_to_json(prices, updated_at)
    save_to_spreadsheet(prices, date_str)

    print("\n=== 完了 ===")

if __name__ == "__main__":
    main()
