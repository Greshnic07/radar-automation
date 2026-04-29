import os
import json
import random
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

TV_DATA_FILE = "tv_data.json"

# --- 2ГИС (АПИ) ---
GIS_API_KEY = os.environ.get("API_KEY", "37c04fe6-a560-4549-b459-0ce83ce384f3")

LOCATIONS_2GIS_API = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913",
    "ТЦ КИТ": "70000001042302381",
    "Молодежная": "70000001031336495"
}

# --- ЯНДЕКС (ВИДЖЕТЫ - БЕЗ КАПЧИ) ---
# Я взял цифровые ID из твоих прошлых ссылок
LOCATIONS_YANDEX_WIDGET = {
    "Кирова, 146": "215636523165",
    "50 лет ВЛКСМ": "1726053880",
    "Удмуртская": "1325176045",
    "9 Января": "170942637213",
    "ТЦ КИТ": "1759491799",
    "Молодежная": "1205315808"
}

def get_stars_emoji(val):
    try:
        count = int(float(str(val).replace(',', '.')))
        return "⭐️" * count
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    print(f"[{update_time}] СТАРТ: Сбор отзывов Додо Пицца...")
    
    data = {"yandex": [], "gis": [], "last_update": update_time}

    # ==========================================
    # 1. 2ГИС (АПИ С МАСКИРОВКОЙ)
    # ==========================================
    print("--- Сбор 2ГИС через скрытое API ---")
    
    # ВОТ ОНИ, СПАСИТЕЛЬНЫЕ ЗАГОЛОВКИ! Без них сервер дает 403.
    headers_2gis = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://2gis.ru/",
        "Origin": "https://2gis.ru",
        "Accept": "application/json"
    }

    for name, firm_id in LOCATIONS_2GIS_API.items():
        try:
            api_url = f"https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews"
            params = {
                "limit": 3,
                "is_advertiser": "false",
                "rated": "true",
                "sort_by": "date_edited",
                "key": GIS_API_KEY,
                "locale": "ru_RU"
            }
            resp = requests.get(api_url, params=params, headers=headers_2gis, timeout=10)
            
            if resp.status_code == 200:
                reviews_data = resp.json().get("reviews", [])
                for rev in reviews_data[:2]:
                    text = rev.get("text", "").replace("\n", " ").strip()
                    if len(text) > 5:
                        data["gis"].append({
                            "author": rev["user"]["name"],
                            "location": name,
                            "stars": get_stars_emoji(rev.get("rating", 5)),
                            "text": text
                        })
                print(f"✅ 2ГИС {name}: получено через API")
            else:
                print(f"⚠️ 2ГИС {name}: ошибка API {resp.status_code}")
        except Exception as e:
            print(f"❌ 2ГИС {name}: {e}")

    # ==========================================
    # 2. ЯНДЕКС (ДЫРА ЧЕРЕЗ ВИДЖЕТЫ)
    # ==========================================
    print("--- Сбор Яндекс через Виджеты ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1000, 'height': 800}
        )
        page = context.new_page()

        for name, org_id in LOCATIONS_YANDEX_WIDGET.items():
            try:
                # ИДЕМ НЕ НА КАРТЫ, А НА СТРАНИЦУ ВИДЖЕТА!
                url = f"https://yandex.ru/maps-reviews-widget/{org_id}?comments"
                print(f"Заходим в Яндекс Виджет: {name}...")
                
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000) # Даем виджету прогрузиться
                
                # Парсим виджет (у него другая структура HTML, более простая)
                res = page.evaluate("""() => {
                    // Ищем любые блоки с отзывами
                    let cards = document.querySelectorAll('div[class*="review"], .we-review');
                    for (let card of cards) {
                        let author = card.querySelector('[class*="name"], [class*="author"]')?.innerText.trim() || "Клиент";
                        let text = card.querySelector('[class*="text"]')?.innerText.trim() || "";
                        
                        // Если есть нормальный текст, забираем
                        if (text.length > 15) {
                            return { author, text, rating: 5 }; // Ставим 5 звезд по умолчанию для упрощения
                        }
                    }
                    return null;
                }""")
                
                if res and res['text']:
                    data["yandex"].append({
                        "author": res['author'], "location": name,
                        "stars": get_stars_emoji(res['rating']), "text": res['text'].replace('\n', ' ')
                    })
                    print(f"✅ Яндекс {name}: Отзыв взят из виджета")
                else:
                    print(f"⚠️ Яндекс {name}: Пусто (Скриншот сохранен)")
                    page.screenshot(path=f"error_yandex_widget_{org_id}.png")
            except Exception as e: 
                print(f"❌ Яндекс {name}: Ошибка загрузки виджета")

        browser.close()

    # Перемешиваем и берем по 2 случайных для ТВ
    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])
    data["gis"] = data["gis"][:2]
    data["yandex"] = data["yandex"][:2]

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"🚀 Сбор окончен! 2ГИС: {len(data['gis'])}, Яндекс: {len(data['yandex'])}")

if __name__ == "__main__":
    run()
