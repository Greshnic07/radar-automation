import os
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

TV_DATA_FILE = "tv_data.json"
API_KEY_2GIS = "37c04fe6-a560-4549-b459-02309cf643ad"

LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913"
}

def run():
    print(f"[{datetime.now()}] Прорыв блокады Яндекса...")
    data = {"yandex": [], "gis": []}

    # 1. СБОР 2ГИС (Работает железно)
    print("Собираем 2ГИС...")
    for name, firm_id in LOCATIONS_2GIS.items():
        try:
            url = f"https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews?limit=1&key={API_KEY_2GIS}&locale=ru_RU"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                revs = r.json().get("reviews", [])
                if revs:
                    data["gis"].append({
                        "author": revs[0].get("user", {}).get("name", "Клиент"),
                        "location": name,
                        "stars": "⭐️" * revs[0].get("rating", 5),
                        "text": revs[0].get("text", "Отзыв без текста").replace("\n", " ")
                    })
        except: continue

    # 2. СБОР ЯНДЕКС (Боевой вылет)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="ru-RU"
        )
        page = context.new_page()
        try:
            print("Открываем Яндекс Карты...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="domcontentloaded", timeout=60000)
            
            # Ждем и убираем плашку Cookies, если она есть
            page.wait_for_timeout(3000)
            cookie_button = page.locator("button:has-text('Allow all'), button:has-text('Принять все')")
            if cookie_button.is_visible():
                cookie_button.click()
                print("🍪 Плашка Cookies убрана")

            # Листаем чуть-чуть, чтобы Яндекс подумал, что мы читаем
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(2000)

            # Ищем отзывы (используем несколько селекторов для надежности)
            review_selector = ".business-review-view__body-text, [itemprop='reviewBody'], .business-reviews-card-view__review-text"
            page.wait_for_selector(review_selector, timeout=20000)
            
            texts = page.locator(review_selector).all_inner_texts()
            authors = page.locator(".business-review-view__author-name, .business-reviews-card-view__author-name").all_inner_texts()

            for i in range(min(2, len(texts))):
                data["yandex"].append({
                    "author": authors[i] if i < len(authors) else "Клиент Додо",
                    "location": "Ижевск, ул. Кирова",
                    "stars": "⭐️⭐️⭐️⭐️⭐️",
                    "text": texts[i].strip()
                })
            print("✅ Яндекс сдался и отдал отзывы!")

        except Exception as e:
            print(f"⚠️ Яндекс опять хитрит: {e}")
            page.screenshot(path="yandex_fail.png") # На всякий случай сделаем новый скрин
            if not data["yandex"]:
                data["yandex"] = [{"author": "Система", "location": "Яндекс", "stars": "", "text": "Яндекс временно недоступен, но мы его доломаем!"}]
        
        browser.close()

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 Данные сохранены. Проверяй телек через минуту!")

if __name__ == "__main__":
    run()
