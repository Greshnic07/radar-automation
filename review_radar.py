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
    "Кирова, 146": "70000001083938641"
}

def run():
    print(f"[{datetime.now()}] Попытка прорыва Яндекса...")
    
    data = {"yandex": [], "gis": []}

    # 1. 2ГИС (уже работает, не трогаем)
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
                        "text": revs[0].get("text", "").replace("\n", " ")
                    })
        except: continue

    # 2. ЯНДЕКС (Боевой режим)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Подменяем всё: от языка до платформы
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow"
        )
        page = context.new_page()
        
        try:
            # Пробуем прямую ссылку на отзывы конкретной Додо Пиццы
            print("Заходим на Яндекс...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="networkidle", timeout=60000)
            
            # Ждем чуть-чуть, имитируем чтение
            page.wait_for_timeout(7000)
            
            # Если не находим отзывы, делаем скриншот перед выходом
            try:
                page.wait_for_selector(".business-review-view__body-text", timeout=15000)
                
                texts = page.locator(".business-review-view__body-text").all_inner_texts()
                authors = page.locator(".business-review-view__author-name").all_inner_texts()

                for i in range(min(2, len(texts))):
                    data["yandex"].append({
                        "author": authors[i] if i < len(authors) else "Клиент",
                        "location": "Додо Пицца",
                        "stars": "⭐️⭐️⭐️⭐️⭐️",
                        "text": texts[i].strip()
                    })
                print("✅ Яндекс пробит!")
            except:
                print("⚠️ Селектор не найден, сохраняю скриншот 'yandex_fail.png'...")
                page.screenshot(path="yandex_fail.png")
                data["yandex"] = [{"author": "Яндекс", "location": "Заблокировано", "stars": "", "text": "Яндекс требует капчу. Проверь файл yandex_fail.png в репозитории."}]

        except Exception as e:
            print(f"❌ Ошибка Яндекса: {e}")
        
        browser.close()

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run()
