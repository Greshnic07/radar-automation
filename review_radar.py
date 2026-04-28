import time
import os
import requests
import re
import hashlib
import json # <--- ДОБАВЛЕН ИМПОРТ ДЛЯ ТЕЛЕВИЗОРА
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Загружаем переменные (если есть .env)
load_dotenv()

# ==========================================================
# ===                    НАСТРОЙКИ                       ===
# ==========================================================

TG_TOKEN = "8752060052:AAGCGETFbDDBW9i-2ZTIHXsVBIJW5yWPnHU"
TG_CHAT_ID = "908428358"
API_KEY_2GIS = os.getenv("API_KEY", "37c04fe6-a560-4549-b459-02309cf643ad")

# === 2ГИС (РАБОТАЕТ ЧЕРЕЗ API ПО ID ФИЛИАЛА) ===
LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913",
    "Ленина, 138": "70000001061227459",
    "Гагарина, 27": "70000001053699613",
    "Сарапул Горького, 16": "70000001039109949"
}

# === ЯНДЕКС КАРТЫ (РАБОТАЕТ ЧЕРЕЗ SELENIUM ПО URL) ===
LOCATIONS_YANDEX = {
    "50 лет ВЛКСМ, 49": "https://yandex.ru/maps/org/dodo_pitstsa/50127051254/reviews/?display-text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F&ll=53.244562%2C56.859157&mode=search&sll=53.235807%2C56.840237&tab=reviews&text=chain_id%3A%2870891266502%29&z=13",
    "9 Января, 219А": "https://yandex.ru/maps/org/dodo_pitstsa/52240577233/reviews/?display-text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F&ll=53.244390%2C56.861884&mode=search&sctx=ZAAAAAgBEAAaKAoSCadbdoh%2FmkpAERBAahMnbUxAEhIJSIszhjlB2D8Rz2vsEtVb0T8iBgABAgMEBSgAOABAkowGSAFiOnJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9FbmFibGVkPTFiOnJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9NYXhhZHY9MTViRHJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9SZWdpb25JZHM9WzEsMTAxNzRdYlhyZWFycj1zY2hlbWVfTG9jYWwvR2VvL0FkdmVydHMvUmVhcnJhbmdlQnlBdWN0aW9uL1NpbWlsYXJPcmdzTGlzdEF1Y3Rpb24vUGFnZUlkPTE5MDkyMDQwYkByZWFycj1zY2hlbWVfTG9jYWwvR2VvdXBwZXIvQWR2ZXJ0cy9NYXhhZHZUb3BNaXgvTWF4YWR2Rm9yTWl4PTEwagJydZ0BzczMPaABAKgBAL0BoswK1cIBJJ3xwKejBtHln87CAZ%2B3%2F8LAAfazuN66AcPYtfnkBeyOksyVBIICFmNoYWluX2lkOig3MDg5MTI2NjUwMimKAgCSAgCaAgxkZXNrdG9wLW1hcHPaAigKEgl9lXzsLp5KQBGQ6T%2FljmtMQBISCQDQDOIDO8g%2FEQB%2FjT3eWME%2F4AIB&sll=53.244390%2C56.861884&sspn=0.174408%2C0.078326&tab=reviews&text=chain_id%3A%2870891266502%29&z=13",
    "ул. Кирова, 146": "https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/?display-text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F&ll=53.244390%2C56.861884&mode=search&sctx=ZAAAAAgBEAAaKAoSCadbdoh%2FmkpAERBAahMnbUxAEhIJSIszhjlB2D8Rz2vsEtVb0T8iBgABAgMEBSgAOABAkowGSAFiOnJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9FbmFibGVkPTFiOnJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9NYXhhZHY9MTViRHJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9SZWdpb25JZHM9WzEsMTAxNzRdYlhyZWFycj1zY2hlbWVfTG9jYWwvR2VvL0FkdmVydHMvUmVhcnJhbmdlQnlBdWN0aW9uL1NpbWlsYXJPcmdzTGlzdEF1Y3Rpb24vUGFnZUlkPTE5MDkyMDQwYkByZWFycj1zY2hlbWVfTG9jYWwvR2VvdXBwZXIvQWR2ZXJ0cy9NYXhhZHZUb3BNaXgvTWF4YWR2Rm9yTWl4PTEwagJydZ0BzczMPaABAKgBAL0BoswK1cIBJJ3xwKejBtHln87CAZ%2B3%2F8LAAfazuN66AcPYtfnkBeyOksyVBIICFmNoYWluX2lkOig3MDg5MTI2NjUwMimKAgCSAgCaAgxkZXNrdG9wLW1hcHPaAigKEgl9lXzsLp5KQBGQ6T%2FljmtMQBISCQDQDOIDO8g%2FEQB%2FjT3eWME%2F4AIB&sll=53.244390%2C56.861884&sspn=0.174408%2C0.078326&tab=reviews&text=chain_id%3A%2870891266502%29&z=13",
    "Ленина, 138": "https://yandex.ru/maps/org/dodo_pitstsa/198896872515/reviews/?display-text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F&ll=53.255548%2C56.842603&mode=search&sctx=ZAAAAAgBEAAaKAoSCadbdoh%2FmkpAERBAahMnbUxAEhIJSIszhjlB2D8Rz2vsEtVb0T8iBgABAgMEBSgAOABALEgBYjpyZWFycj1zY2hlbWVfTG9jYWwvR2VvdXBwZXIvQWR2ZXJ0cy9DdXN0b21NYXhhZHYvRW5hYmxlZD0xYjpyZWFycj1zY2hlbWVfTG9jYWwvR2VvdXBwZXIvQWR2ZXJ0cy9DdXN0b21NYXhhZHYvTWF4YWR2PTE1YkRyZWFycj1zY2hlbWVfTG9jYWwvR2VvdXBwZXIvQWR2ZXJ0cy9DdXN0b21NYXhhZHYvUmVnaW9uSWRzPVsxLDEwMTc0XWJYcmVhcnI9c2NoZW1lX0xvY2FsL0dlby9BZHZlcnRzL1JlYXJyYW5nZUJ5QXVjdGlvbi9TaW1pbGFyT3Jnc0xpc3RBdWN0aW9uL1BhZ2VJZD0xOTA5MjA0MGJAcmVhcnI9c2NoZW1lX0xvY2FsL0dlb3VwcGVyL0FkdmVydHMvTWF4YWR2VG9wTWl4L01heGFkdkZvck1peD0xMGoCcnWdAc3MzD2gAQCoAQC9AaLMCtXCAR6d8cCnowbD2LX55AXR5Z%2FOwgGft%2F%2FCwAH2s7jeugGCAhZjaGFpbl9pZDooNzA4OTEyNjY1MDIpigIAkgIAmgIMZGVza3RvcC1tYXBzqgILNzA4OTEyNjY1MDKwAgHaAigKEgkgJXZtb6FKQBGKISar6WxMQBISCQCUFFgAU8Y%2FEQBApN%2B%2BDrQ%2F4AIB&sll=53.255548%2C56.842603&sspn=0.174408%2C0.078367&tab=reviews&text=chain_id%3A%2870891266502%29&z=13",
    "Гагарина, 27": "https://yandex.ru/maps/org/dodo_pitstsa/143235778412/reviews/?display-text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F&ll=53.182077%2C56.804953&mode=search&sctx=ZAAAAAgBEAAaKAoSCadbdoh%2FmkpAERBAahMnbUxAEhIJSIszhjlB2D8Rz2vsEtVb0T8iBgABAgMEBSgAOABAw58NSAFiOnJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9FbmFibGVkPTFiOnJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9NYXhhZHY9MTViRHJlYXJyPXNjaGVtZV9Mb2NhbC9HZW91cHBlci9BZHZlcnRzL0N1c3RvbU1heGFkdi9SZWdpb25JZHM9WzEsMTAxNzRdYlhyZWFycj1zY2hlbWVfTG9jYWwvR2VvL0FkdmVydHMvUmVhcnJhbmdlQnlBdWN0aW9uL1NpbWlsYXJPcmdzTGlzdEF1Y3Rpb24vUGFnZUlkPTE5MDkyMDQwYkByZWFycj1zY2hlbWVfTG9jYWwvR2VvdXBwZXIvQWR2ZXJ0cy9NYXhhZHZUb3BNaXgvTWF4YWR2Rm9yTWl4PTEwagJydZ0BzczMPaABAKgBAL0BoswK1cIBGOyOksyVBJ3xwKejBp%2B3%2F8LAAcPYtfnkBYICFmNoYWluX2lkOig3MDg5MTI2NjUwMimKAgCSAgCaAgxkZXNrdG9wLW1hcHOqAgs3MDg5MTI2NjUwMrACAdoCKAoSCbfrpSkCmkpAEf7NLJTaaUxAEhIJAJQUWABTxj8RAKQBvAUStD%2FgAgE%3D&sll=53.182077%2C56.804953&sspn=0.174408%2C0.078446&tab=reviews&text=chain_id%3A%2870891266502%29&z=13",
    "Сарапул Горького, 16": "https://yandex.ru/maps/org/dodo_pitstsa/1084947947/reviews/?ll=53.812595%2C56.476065&mode=search&sll=53.182077%2C56.804953&sspn=0.174408%2C0.078446&tab=reviews&text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%A1%D0%B0%D1%80%D0%B0%D0%BF%D1%83%D0%BB&z=17",
    "Удмуртская, 304": "https://yandex.ru/maps/org/dodo_pitstsa/51680107423/reviews/?ll=53.229449%2C56.861615&mode=search&sll=53.223620%2C56.860847&sspn=0.028817%2C0.009392&tab=reviews&text=%D0%94%D0%BE%D0%B4%D0%BE%20%D0%9F%D0%B8%D1%86%D1%86%D0%B0%20%D0%B8%D0%B6%D0%B5%D0%B2%D1%81%D0%BA&z=15.41"
}

DB_FILE = "reviews_hashes_combo.txt"
CHECK_INTERVAL = 3600
TV_DATA_FILE = "tv_data.json" # <--- Файл для ТВ

HEADERS_2GIS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# ==========================================================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    proxies = {"http": "socks5h://127.0.0.1:10808", "https": "socks5h://127.0.0.1:10808"}
    
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}, proxies=proxies, timeout=20)
    except Exception as e:
        print(f"❌ Ошибка отправки в ТГ: {e}")

def get_stars_emoji(rating):
    try:
        r = int(float(str(rating).replace(',', '.')))
        return "⭐️" * r
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

# ----------------------------------------------------------
# ПАРСЕР 2ГИС (СВЕРХБЫСТРЫЙ API)
# ----------------------------------------------------------
def get_last_review_2gis(firm_id, name):
    api_url = f"https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews"
    params = {
        "limit": 1,
        "offset": 0,
        "is_advertiser": "false",
        "fields": "meta.providers,meta.branch_rating,meta.branch_reviews_count,meta.total_count,reviews.hiding_reason,reviews.is_verified,reviews.emojis",
        "without_my_first_review": "false",
        "rated": "true",
        "sort_by": "date_edited",
        "key": API_KEY_2GIS,
        "locale": "ru_RU"
    }

    try:
        resp = requests.get(api_url, params=params, headers=HEADERS_2GIS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            reviews = data.get("reviews", [])
            if reviews:
                review = reviews[0]
                return {
                    "text": review.get("text", "").replace("\n", " ").strip(),
                    "rating": review.get("rating", 5),
                    "author": review.get("user", {}).get("name", "Аноним")
                }
    except Exception as e:
        print(f"❌ Ошибка 2ГИС {name}: {e}")
    return None

# ----------------------------------------------------------
# ПАРСЕР ЯНДЕКС (БРОНЕБОЙНЫЙ SELENIUM JS-INJECTION)
# ----------------------------------------------------------
def get_last_review_yandex(driver, url, name):
    if "URL_ЯНДЕКСА" in url: return None
        
    try:
        driver.get(url)
        print(f"🌐 {name} (Яндекс): Загрузка (фоновый режим)...")
        time.sleep(12) 

        driver.execute_script("""
            let scrollables = document.querySelectorAll('.scroll__container, .sidebar-view, .scroll__view');
            scrollables.forEach(el => el.scrollTop = 800);
            window.scrollBy(0, 800);
        """)
        time.sleep(3)

        driver.execute_script("""
            let review = document.querySelector('[itemprop="review"]') || document.querySelector('.business-review-view');
            if (!review) return;
            let clickables = review.querySelectorAll('span, a, div, button');
            for (let el of clickables) {
                let txt = el.textContent.trim();
                if (txt === 'Читать целиком' || txt === 'Ещё' || txt === 'Развернуть') { el.click(); }
            }
        """)
        time.sleep(1) 

        data = driver.execute_script("""
            let review = document.querySelector('[itemprop="review"]') || document.querySelector('.business-review-view') || document.querySelector('.business-reviews-card-view__review');
            if (!review) return null;

            let textEl = review.querySelector('[itemprop="reviewBody"]') || review.querySelector('.business-review-view__body-text') || review.querySelector('.business-review-view__text');
            let text = textEl ? textEl.innerText.trim() : review.innerText.trim();

            let authorEl = review.querySelector('[itemprop="name"]') || review.querySelector('.business-review-view__author-name');
            let author = authorEl ? authorEl.innerText.trim() : "Аноним";

            let rating = "5"; 
            let ratingMeta = review.querySelector('[itemprop="ratingValue"]');
            if (ratingMeta && ratingMeta.getAttribute('content')) {
                rating = ratingMeta.getAttribute('content');
            } else {
                let starsContainer = review.querySelector('.business-rating-badge-view__stars') || review.querySelector('.business-review-view__rating') || review;
                let allStars = starsContainer.querySelectorAll('svg, .inline-image_icon_star');
                let filledStarsCount = 0;
                allStars.forEach(star => {
                    let html = star.outerHTML.toLowerCase();
                    if (!html.includes('empty') && !html.includes('#ececec') && !html.includes('fill="none"')) {
                        filledStarsCount++;
                    }
                });
                if (filledStarsCount > 0 && filledStarsCount <= 5) rating = filledStarsCount.toString();
            }
            return { text: text, author: author, rating: rating };
        """)

        if data and data['text'] and len(data['text']) > 2:
            clean_text = re.sub(r'(\s*…?\s*Читать целиком|\s*…?\s*Ещё|\s\.+)$', '', data['text']).strip()
            return {"text": clean_text, "rating": data['rating'], "author": data['author']}
        
        return None
    except Exception as e:
        print(f"⚠️ Ошибка Яндекс {name}: {e}")
        return None

# ----------------------------------------------------------
# ОСНОВНОЙ ЦИКЛ
# ----------------------------------------------------------
def main():
    print("💎 РАДАР Додо Пицца: 2GIS API + YANDEX SELENIUM (С ПОДДЕРЖКОЙ ТВ) 💎")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1600,1000")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f: f.write("")

    # --- ИНИЦИАЛИЗАЦИЯ ИСТОРИИ ДЛЯ ТЕЛЕВИЗОРА ---
    tv_history = {"yandex": [], "gis": []}
    if os.path.exists(TV_DATA_FILE):
        try:
            with open(TV_DATA_FILE, "r", encoding="utf-8") as f:
                tv_history = json.load(f)
        except: pass

    while True:
        driver = webdriver.Chrome(options=chrome_options)
        with open(DB_FILE, "r", encoding="utf-8") as f:
            existing_hashes = set(line.strip() for line in f)

        print("\n--- 🟢 ПРОВЕРКА 2ГИС ---")
        for name, firm_id in LOCATIONS_2GIS.items():
            res = get_last_review_2gis(firm_id, name)
            if res:
                r_hash = hashlib.md5(f"2gis{name}{res['text']}".encode('utf-8')).hexdigest()
                if r_hash not in existing_hashes:
                    stars = get_stars_emoji(res["rating"])
                    # Отправка в Телегу без лишних слов
                    msg = f"<b>[2ГИС] {name}</b>\n{stars}\n👤 <b>{res['author']}</b>\n\n{res['text']}"
                    send_telegram(msg)
                    
                    with open(DB_FILE, "a", encoding="utf-8") as f: f.write(f"{r_hash}\n")
                    existing_hashes.add(r_hash)
                    print(f"✅ [2ГИС] НОВЫЙ: {name}")

                    # --- ЗАПИСЬ ДЛЯ ТЕЛЕВИЗОРА ---
                    tv_history["gis"].insert(0, {"author": res["author"], "location": name, "stars": stars, "text": res["text"]})
                    tv_history["gis"] = tv_history["gis"][:2] # Храним только 2 последних
                    with open(TV_DATA_FILE, "w", encoding="utf-8") as json_file:
                        json.dump(tv_history, json_file, ensure_ascii=False, indent=4)
                else:
                    print(f"🤷‍♂️ [2ГИС] Старый: {name}")

        print("\n--- 🔴 ПРОВЕРКА ЯНДЕКС ---")
        for name, url in LOCATIONS_YANDEX.items():
            res = get_last_review_yandex(driver, url, name)
            if res:
                r_hash = hashlib.md5(f"yandex{name}{res['text']}".encode('utf-8')).hexdigest()
                if r_hash not in existing_hashes:
                    stars = get_stars_emoji(res["rating"])
                    # Отправка в Телегу без лишних слов
                    msg = f"<b>[Яндекс] {name}</b>\n{stars}\n👤 <b>{res['author']}</b>\n\n{res['text']}"
                    send_telegram(msg)
                    
                    with open(DB_FILE, "a", encoding="utf-8") as f: f.write(f"{r_hash}\n")
                    existing_hashes.add(r_hash)
                    print(f"✅ [ЯНДЕКС] НОВЫЙ: {name}")

                    # --- ЗАПИСЬ ДЛЯ ТЕЛЕВИЗОРА ---
                    tv_history["yandex"].insert(0, {"author": res["author"], "location": name, "stars": stars, "text": res["text"]})
                    tv_history["yandex"] = tv_history["yandex"][:2] # Храним только 2 последних
                    with open(TV_DATA_FILE, "w", encoding="utf-8") as json_file:
                        json.dump(tv_history, json_file, ensure_ascii=False, indent=4)
                else:
                    print(f"🤷‍♂️ [ЯНДЕКС] Старый: {name}")

        driver.quit()
        print(f"\n💤 Все точки проверены. Спим {CHECK_INTERVAL // 60} мин...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()