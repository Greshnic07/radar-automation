import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

TV_DATA_FILE = "tv_data.json"
API_KEY_2GIS = "37c04fe6-a560-4549-b459-02309cf643ad"

def run():
    print(f"[{datetime.now()}] Сбор данных для ТВ...")
    
    # Данные по умолчанию
    data = {
        "yandex": [{"author": "Система", "location": "Яндекс", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Яндекс проверяется..."}],
        "gis": [{"author": "Система", "location": "2ГИС", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "2ГИС проверяется..."}]
    }

    # 1. Сначала берем 2ГИС (он самый надежный)
    try:
        # ID точки на 50 лет ВЛКСМ
        url_2gis = f"https://public-api.reviews.2gis.com/2.0/branches/70000001045878325/reviews?limit=2&key={API_KEY_2GIS}&locale=ru_RU"
        r = requests.get(url_2gis, timeout=10)
        if r.status_code == 200:
            reviews = r.json().get("reviews", [])
            data["gis"] = []
            for rev in reviews[:2]:
                data["gis"].append({
                    "author": rev.get("user", {}).get("name", "Клиент"),
                    "location": "Додо Пицца",
                    "stars": "⭐️" * rev.get("rating", 5),
                    "text": rev.get("text", "Отзыв без текста").replace("\n", " ")
                })
            print("✅ 2ГИС успешно собран")
    except Exception as e:
        print(f"❌ Ошибка 2ГИС: {e}")

    # 2. Пробуем Яндекс
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        try:
            # Ссылка на отзывы (ул. Кирова)
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="networkidle", timeout=60000)
            page.wait_for_selector(".business-review-view__body-text", timeout=20000)
            
            texts = page.locator(".business-review-view__body-text").all_inner_texts()
            authors = page.locator(".business-review-view__author-name").all_inner_texts()
            
            data["yandex"] = []
            for i in range(min(2, len(texts))):
                data["yandex"].append({
                    "author": authors[i],
                    "location": "Додо Пицца",
                    "stars": "⭐️⭐️⭐️⭐️⭐️",
                    "text": texts[i][:300]
                })
            print("✅ Яндекс успешно собран")
        except Exception as e:
            print(f"⚠️ Яндекс опять заблочил: {e}")
        browser.close()

    # Сохраняем результат
    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 Файл tv_data.json обновлен!")

if __name__ == "__main__":
    run()
