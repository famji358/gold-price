import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# ヘッダー（ブラウザのふりをしてブロックされにくくする）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_price(text):
    """価格テキストから数字だけ取り出す"""
    nums = re.findall(r'[\d,]+', text)
    for n in nums:
        val = int(n.replace(',', ''))
        if 10000 <= val <= 100000:  # 金の1g価格として妥当な範囲
            return val
    return None

def get_tanaka():
    """田中貴金属（ベンチマーク）"""
    try:
        res = requests.get("https://gold.tanaka.co.jp/silver_price/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.select("table tr")
        for row in rows:
            text = row.get_text()
            if "店頭買取価格" in text:
                cells = row.find_all(["td", "th"])
                for cell in cells:
                    price = clean_price(cell.get_text())
                    if price:
                        return price
    except Exception as e:
        print(f"田中貴金属エラー: {e}")
    return None

def get_otakaraya():
    """おたからや"""
    try:
        res = requests.get("https://www.otakaraya.jp/gold/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        el = soup.select_one(".rate-price")
        if el:
            return clean_price(el.get_text())
    except Exception as e:
        print(f"おたからやエラー: {e}")
    return None

def get_daikichi():
    """買取大吉"""
    try:
        res = requests.get("https://daikichi-kaitori.jp/gold/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        el = soup.find(id="bold_bm2025")
        if el:
            return clean_price(el.get_text())
    except Exception as e:
        print(f"買取大吉エラー: {e}")
    return None

def get_nanboya():
    """なんぼや"""
    try:
        res = requests.get("https://nanboya.com/gold-kaitori/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        # 今日の価格が含まれるdivを探す
        for div in soup.find_all("div"):
            text = div.get_text()
            if "今日" in text or "本日" in text:
                price = clean_price(text)
                if price:
                    return price
        # フォールバック：ページ内の妥当な価格を探す
        text = soup.get_text()
        nums = re.findall(r'([\d,]+)円/g', text)
        for n in nums:
            val = int(n.replace(',', ''))
            if 10000 <= val <= 100000:
                return val
    except Exception as e:
        print(f"なんぼやエラー: {e}")
    return None

def get_refasta():
    """リファスタ"""
    try:
        res = requests.get("https://kinkaimasu.jp/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        gold_div = soup.find(id="gold")
        if gold_div:
            el = gold_div.select_one(".big")
            if el:
                return clean_price(el.get_text())
    except Exception as e:
        print(f"リファスタエラー: {e}")
    return None

def get_burariba():
    """ブラリバ（ブランドリバリュー）"""
    try:
        res = requests.get("https://brandrevalue.com/cat/gold/ingot", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        el = soup.select_one(".metal-price-today")
        if el:
            # 金の価格だけ取り出す（最初の妥当な数字）
            return clean_price(el.get_text())
    except Exception as e:
        print(f"ブラリバエラー: {e}")
    return None

def main():
    print("価格取得を開始します...")
    
    results = {
        "updated_at": datetime.now().strftime("%Y年%m月%d日 %H:%M"),
        "prices": [
            {
                "name": "田中貴金属",
                "label": "ベンチマーク（公式相場）",
                "url": "https://gold.tanaka.co.jp/silver_price/",
                "price": get_tanaka(),
                "is_benchmark": True
            },
            {
                "name": "おたからや",
                "label": "",
                "url": "https://lp.otakaraya.jp/lp-gold-b/",
                "price": get_otakaraya(),
                "is_benchmark": False
            },
            {
                "name": "買取大吉",
                "label": "",
                "url": "https://daikichi-kaitori.jp/gold/",
                "price": get_daikichi(),
                "is_benchmark": False
            },
            {
                "name": "なんぼや",
                "label": "",
                "url": "https://nanboya.com/gold-kaitori/",
                "price": get_nanboya(),
                "is_benchmark": False
            },
            {
                "name": "リファスタ",
                "label": "",
                "url": "https://kinkaimasu.jp/",
                "price": get_refasta(),
                "is_benchmark": False
            },
            {
                "name": "ブラリバ",
                "label": "",
                "url": "https://brandrevalue.com/recommend/gold",
                "price": get_burariba(),
                "is_benchmark": False
            },
        ]
    }

    # 価格順に並び替え（ベンチマークは除く、Noneは最後）
    benchmark = [p for p in results["prices"] if p["is_benchmark"]]
    others = [p for p in results["prices"] if not p["is_benchmark"]]
    others_sorted = sorted(others, key=lambda x: x["price"] if x["price"] else 0, reverse=True)
    results["prices"] = benchmark + others_sorted

    # JSONに保存
    with open("gold_prices.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("完了しました。gold_prices.json を確認してください。")
    for p in results["prices"]:
        price_str = f"{p['price']:,}円/g" if p['price'] else "取得失敗"
        print(f"  {p['name']}: {price_str}")

if __name__ == "__main__":
    main()
