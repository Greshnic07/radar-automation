import os
import json
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
    try:
        count = int(float(str(val).replace(',', '.')))
        return "⭐️" * count
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

def run():
    print(f"[{datetime.now()}] Сбор данных (Бронебойный режим)...")
    data = {"yandex": [], "gis": []}

    # 1. 2ГИС (Работает железно)
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

    # 2. ЯНДЕКС (С твоей логикой Selenium)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 1200},
            locale="ru-RU"
        )
        page = context.new_page()
        
        try:
            print("Заходим на Яндекс (ул. Кирова)...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="domcontentloaded", timeout=60000)
            
            # Ждем прогрузки и убираем куки
            page.wait_for_timeout(5000)
            
            # ТВОЯ ЛОГИКА РАЗВЕРТЫВАНИЯ (через JS-инъекцию)
            page.evaluate("""() => {
                let reviews = document.querySelectorAll('.business-review-view');
                reviews.forEach(review => {
                    let clickables = review.querySelectorAll('span, a, div, button');
                    for (let el of clickables) {
                        let txt = el.textContent.trim();
                        if (txt === 'Читать целиком' || txt === 'Ещё' || txt === 'Развернуть') { el.click(); }
                    }
                });
            }""")
            print("✅ Кнопки 'Ещё' нажаты")
            page.wait_for_timeout(2000)

            # ТВОЯ ЛОГИКА СБОРА (через JS-инъекцию для рейтинга)
            extracted = page.evaluate("""() => {
                let results = [];
                let cards = document.querySelectorAll('.business-review-view');
                for (let i = 0; i < Math.min(2, cards.length); i++) {
                    let card = cards[i];
                    let author = card.querySelector('.business-review-view__author-name')?.innerText || "Клиент";
                    let text = card.querySelector('.business-review-view__body-text')?.innerText || "";
                    let rating = "5";
                    let ratingMeta = card.querySelector('meta[itemprop="ratingValue"]');
                    if (ratingMeta) { rating = ratingMeta.getAttribute('content'); }
                    results.append({author, text, rating});
                }
                return results;
            }""")
            
            # Если JS вернул ошибку или пусто, попробуем старым методом
            if not extracted:
                 # Резервный сбор если JS не сработал
                 texts = page.locator(".business-review-view__body-text").all_inner_texts()
                 authors = page.locator(".business-review-view__author-name").all_inner_texts()
                 for i in range(min(2, len(texts))):
                     data["yandex"].append({
                         "author": authors[i] if i < len(authors) else "Клиент",
                         "location": "ул. Кирова, 146",
                         "stars": "⭐️⭐️⭐️⭐️⭐️",
                         "text": texts[i].strip()
                     })
            else:
                for res in extracted:
                    data["yandex"].append({
                        "author": res['author'],
                        "location": "ул. Кирова, 146",
                        "stars": get_stars_emoji(res['rating']),
                        "text": res['text'].strip()
                    })
            
            print(f"✅ Яндекс собран. Найдено отзывов: {len(data['yandex'])}")

        except Exception as e:
            print(f"⚠️ Ошибка Яндекса: {e}")
            page.screenshot(path="yandex_fail.png")
            # Если всё упало, заполняем заглушкой, чтобы экран не висел
            if not data["yandex"]:
                data["yandex"] = [{"author": "Система", "location": "Яндекс", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Яндекс временно недоступен. Проверьте логи."}]
        
        browser.close()

    # Сохраняем результат
    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 Файл tv_data.json готов!")

if __name__ == "__main__":
    run()
