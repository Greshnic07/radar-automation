import os
import json
import random
import requests
import urllib.parse
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

TV_DATA_FILE = "tv_data.json"
GIS_API_KEY = os.environ.get("API_KEY", "37c04fe6-a560-4549-b459-0ce83ce384f3")

LOCATIONS_2GIS_API = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913",
    "ТЦ КИТ": "70000001042302381",
    "Молодежная": "70000001031336495"
}

# Возвращаем основные Карты Яндекса
LOCATIONS_YANDEX = {
    "Кирова, 146": "https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/",
    "50 лет ВЛКСМ": "https://yandex.ru/maps/org/dodo_pitstsa/1726053880/reviews/",
    "Удмуртская": "https://yandex.ru/maps/org/dodo_pitstsa/1325176045/reviews/",
    "9 Января": "https://yandex.ru/maps/org/dodo_pitstsa/170942637213/reviews/",
    "ТЦ КИТ": "https://yandex.ru/maps/org/dodo_pitstsa/1759491799/reviews/",
    "Молодежная": "https://yandex.ru/maps/org/dodo_pitstsa/1205315808/reviews/"
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
    # 1. 2ГИС (ЧЕРЕЗ БЕСПЛАТНЫЙ ПРОКСИ-ШЛЮЗ)
    # ==========================================
    print("--- Сбор 2ГИС (Обход бана по IP) ---")
    for name, firm_id in LOCATIONS_2GIS_API.items():
        try:
            api_url = f"https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews"
            params = {
                "limit": "3",
                "is_advertiser": "false",
                "rated": "true",
                "sort_by": "date_edited",
                "key": GIS_API_KEY,
                "locale": "ru_RU"
            }
            full_url = api_url + "?" + urllib.parse.urlencode(params)
            
            # Используем публичные CORS-шлюзы как бесплатные прокси!
            proxy_urls = [
                f"https://api.allorigins.win/raw?url={urllib.parse.quote(full_url)}",
                f"https://corsproxy.io/?url={urllib.parse.quote(full_url)}"
            ]
            
            success = False
            for p_url in proxy_urls:
                resp = requests.get(p_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=15)
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
                    print(f"✅ 2ГИС {name}: пробито через шлюз")
                    success = True
                    break
            
            if not success:
                print(f"⚠️ 2ГИС {name}: Ошибка доступа к API")
        except Exception as e:
            print(f"❌ 2ГИС {name}: {e}")

    # ==========================================
    # 2. ЯНДЕКС (БРАУЗЕР FIREFOX)
    # ==========================================
    print("--- Сбор Яндекс через Firefox ---")
    with sync_playwright() as p:
        # ЗАМЕНА CHROMIUM НА FIREFOX — ломаем скрипты Яндекса!
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            viewport={'width': 1366, 'height': 768},
            locale="ru-RU"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        for name, url in LOCATIONS_YANDEX.items():
            try:
                print(f"Заходим в Яндекс: {name}...")
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3500)
                
                page.evaluate("""() => {
                    let buttons = document.querySelectorAll('.business-review-view__body-expand, .business-review-view__expand');
                    buttons.forEach(b => b.click());
                }""")
                page.wait_for_timeout(1000)
                
                res = page.evaluate("""() => {
                    let card = document.querySelector('.business-review-view');
                    if (!card) return null;
                    let author = card.querySelector('.business-review-view__author-name')?.innerText.trim() || "Клиент";
                    let text = card.querySelector('.business-review-view__body-text')?.innerText.trim() || "";
                    let stars = card.querySelectorAll('.business-rating-badge-view__star._filled').length || 5;
                    return { author, text, rating: stars };
                }""")
                
                if res and res['text']:
                    data["yandex"].append({
                        "author": res['author'], "location": name,
                        "stars": get_stars_emoji(res['rating']), "text": res['text'].replace('\n', ' ')
                    })
                    print(f"✅ Яндекс {name}: Отзыв взят")
                else:
                    print(f"⚠️ Яндекс {name}: Пусто (Скрин сохранен)")
                    page.screenshot(path=f"error_yandex_{name}.png")
            except Exception as e: 
                print(f"❌ Яндекс {name}: Ошибка")

        browser.close()

    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])
    data["gis"] = data["gis"][:2]
    data["yandex"] = data["yandex"][:2]

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"🚀 Сбор окончен! 2ГИС: {len(data['gis'])}, Яндекс: {len(data['yandex'])}")

if __name__ == "__main__":
    run()
