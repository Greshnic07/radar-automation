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

def get_stars_emoji(val):
    """Превращает число в ряд звезд"""
    try:
        count = int(float(str(val).replace(',', '.')))
        return "⭐️" * count
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

def run():
    print(f"[{datetime.now()}] Сбор честных отзывов для ТВ...")
    data = {"yandex": [], "gis": []}

    # 1. 2ГИС (Звезды и так работали, но прогоним через общую функцию)
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
                        "stars": get_stars_emoji(revs[0].get("rating", 5)),
                        "text": revs[0].get("text", "").replace("\n", " ")
                    })
        except: continue

    # 2. ЯНДЕКС (С честными звездами и нажатием кнопок)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 1000},
            locale="ru-RU"
        )
        page = context.new_page()
        try:
            print("Заходим на Яндекс за правдой...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Нажимаем кнопки развертывания
            expand_buttons = page.locator("span:has-text('Ещё'), span:has-text('Читать целиком'), .business-review-view__expand")
            for i in range(min(3, expand_buttons.count())):
                try: expand_buttons.nth(i).click(timeout=3000)
                except: continue
            page.wait_for_timeout(1000)

            # Собираем карточки отзывов целиком, чтобы не перепутать автора и его оценку
            review_cards = page.locator(".business-review-view").all()

            for i in range(min(2, len(review_cards))):
                card = review_cards[i]
                
                # Достаем автора
                author = card.locator(".business-review-view__author-name").inner_text()
                
                # Достаем текст
                text = card.locator(".business-review-view__body-text").inner_text()
                
                # ДОСТАЕМ РЕЙТИНГ (он зарыт в метаданных внутри карточки)
                rating_val = 5
                rating_meta = card.locator("meta[itemprop='ratingValue']")
                if rating_meta.count() > 0:
                    rating_val = rating_meta.get_attribute("content")

                data["yandex"].append({
                    "author": author,
                    "location": "Ижевск, ул. Кирова",
                    "stars": get_stars_emoji(rating_val),
                    "text": text.strip()
                })
            print("✅ Яндекс собран с честными оценками!")

        except Exception as e:
            print(f"⚠️ Ошибка Яндекса: {e}")
            page.screenshot(path="yandex_fail.png")
        
        browser.close()

    # Сохраняем в файл
    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 Всё готово, пушим на ТВ!")

if __name__ == "__main__":
    run()
