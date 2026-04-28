import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

TV_DATA_FILE = "tv_data.json"
API_KEY_2GIS = "37c04fe6-a560-4549-b459-02309cf643ad"

# Точки для 2ГИС (твои проверенные ID)
LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913"
}

def get_stars_emoji(val):
    try:
        count = int(float(str(val).replace(',', '.')))
        return "⭐️" * count
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

def run():
    print(f"[{datetime.now()}] Запуск обновленного парсера (кнопки + звезды)...")
    data = {"yandex": [], "gis": []}

    # 1. 2ГИС (API — работает стабильно)
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

    # 2. ЯНДЕКС (Playwright с твоей логикой Selenium)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 1200},
            locale="ru-RU"
        )
        page = context.new_page()
        
        try:
            print("Открываем Яндекс (ул. Кирова)...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="networkidle", timeout=60000)
            
            # Убираем куки, чтобы не перекрывали кнопки
            page.wait_for_timeout(2000)
            cookie_btn = page.locator("button:has-text('Allow all'), button:has-text('Принять все')")
            if cookie_btn.is_visible():
                cookie_btn.click()

            # ЛОГИКА НАЖАТИЯ (как в твоем старом коде)
            # Ищем все возможные варианты кнопок развертывания
            expand_selectors = [
                "span:has-text('Ещё')", 
                "span:has-text('Читать целиком')", 
                "span:has-text('Развернуть')",
                ".business-review-view__expand"
            ]
            
            for selector in expand_selectors:
                buttons = page.locator(selector)
                count = buttons.count()
                for i in range(min(5, count)):
                    try:
                        buttons.nth(i).click(timeout=2000)
                        page.wait_for_timeout(300)
                    except: continue

            # СБОР ДАННЫХ (с честными звездами через ratingValue)
            review_cards = page.locator(".business-review-view, .business-reviews-card-view__review").all()
            
            for i in range(min(2, len(review_cards))):
                card = review_cards[i]
                
                # Автор
                author = "Клиент"
                author_el = card.locator(".business-review-view__author-name, .business-reviews-card-view__author-name")
                if author_el.count() > 0:
                    author = author_el.first.inner_text()

                # Текст (уже развернутый)
                text = card.locator(".business-review-view__body-text, .business-reviews-card-view__review-text").first.inner_text()
                
                # Оценка (ищем рейтинг в метаданных или считаем звезды)
                rating = 5
                rating_meta = card.locator("meta[itemprop='ratingValue']")
                if rating_meta.count() > 0:
                    rating = rating_meta.get_attribute("content")
                else:
                    # Если мета-тега нет, попробуем найти цифру в классе или атрибутах
                    rating_attr = card.get_attribute("data-rating")
                    if rating_attr: rating = rating_attr

                data["yandex"].append({
                    "author": author.strip(),
                    "location": "ул. Кирова, 146",
                    "stars": get_stars_emoji(rating),
                    "text": text.strip()
                })
            
            print("✅ Яндекс обработан: кнопки нажаты, звезды посчитаны.")

        except Exception as e:
            print(f"⚠️ Ошибка Яндекса: {e}")
            page.screenshot(path="yandex_fail.png")
        
        browser.close()

    # Сохраняем результат для index.html
    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 Файл tv_data.json обновлен. GitHub сейчас вытолкнет его на сайт.")

if __name__ == "__main__":
    run()
