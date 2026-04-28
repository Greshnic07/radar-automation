import os
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

TV_DATA_FILE = "tv_data.json"
API_KEY_2GIS = "37c04fe6-a560-4549-b459-02309cf643ad"

def run():
    print(f"[{datetime.now()}] Сбор данных для ТВ (с маскировкой)...")
    
    data = {
        "yandex": [{"author": "Система", "location": "Яндекс", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Яндекс пока не отдал данные. Пробуем еще раз..."}],
        "gis": []
    }

    # 1. 2ГИС (Работает стабильно)
    try:
        url_2gis = f"https://public-api.reviews.2gis.com/2.0/branches/70000001045878325/reviews?limit=2&key={API_KEY_2GIS}&locale=ru_RU"
        r = requests.get(url_2gis, timeout=10)
        if r.status_code == 200:
            reviews = r.json().get("reviews", [])
            for rev in reviews[:2]:
                data["gis"].append({
                    "author": rev.get("user", {}).get("name", "Клиент"),
                    "location": "Додо Пицца",
                    "stars": "⭐️" * rev.get("rating", 5),
                    "text": rev.get("text", "Без текста").replace("\n", " ")
                })
            print("✅ 2ГИС собран")
    except: print("❌ 2ГИС упал")

    # 2. Яндекс (Пытаемся обмануть)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Добавляем более реалистичный User-Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        try:
            # Идем на Кирова, 146
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="domcontentloaded")
            
            # Имитируем небольшое ожидание и легкий скролл
            page.wait_for_timeout(random.randint(5000, 8000))
            page.mouse.wheel(0, 400)
            
            # Пытаемся найти хотя бы один отзыв
            selector = ".business-review-view__body-text"
            page.wait_for_selector(selector, timeout=25000)
            
            texts = page.locator(selector).all_inner_texts()
            authors = page.locator(".business-review-view__author-name").all_inner_texts()
            
            if texts:
                data["yandex"] = []
                for i in range(min(2, len(texts))):
                    data["yandex"].append({
                        "author": authors[i] if i < len(authors) else "Клиент",
                        "location": "ул. Кирова, 146",
                        "stars": "⭐️⭐️⭐️⭐️⭐️",
                        "text": texts[i][:250].strip() + "..."
                    })
                print("✅ Яндекс пробился!")
        except Exception as e:
            print(f"⚠️ Яндекс опять не пустил. Ошибка: {e}")
        browser.close()

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 Файл обновлен!")

if __name__ == "__main__":
    run()
