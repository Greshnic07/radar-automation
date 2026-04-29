import os
import json
from datetime import datetime, timedelta
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

def take_2gis_screenshot(firm_id, name):
    print(f"📸 Делаем скриншот страницы 2ГИС для {name}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 900}
        )
        page = context.new_page()
        try:
            page.goto(f"https://2gis.ru/firm/{firm_id}/tab/reviews", timeout=30000)
            page.wait_for_timeout(5000) # Ждем прогрузки или капчи
            filename = f"error_2gis_{firm_id}.png"
            page.screenshot(path=filename)
            print(f"✅ Скриншот сохранен: {filename}")
        except Exception as e:
            print(f"❌ Не удалось сделать скриншот: {e}")
        finally:
            browser.close()

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    
    print(f"[{update_time}] Сбор данных (Додо Пицца)...")
    data = {"yandex": [], "gis": [], "last_update": update_time}

    # 1. 2ГИС
    print("Собираем 2ГИС...")
    all_gis = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://2gis.ru/",
        "Accept": "application/json, text/plain, */*"
    }

    for name, firm_id in LOCATIONS_2GIS.items():
        try:
            url = f"https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews?limit=1&key={API_KEY_2GIS}&locale=ru_RU"
            r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code == 200:
                resp_json = r.json()
                revs = resp_json.get("reviews", [])
                
                if revs:
                    all_gis.append({
                        "author": revs[0].get("user", {}).get("name", "Клиент"),
                        "location": name,
                        "stars": get_stars_emoji(revs[0].get("rating", 5)),
                        "text": revs[0].get("text", "").replace("\n", " "),
                        "date": revs[0].get("date_created", "") 
                    })
                    print(f"✅ 2ГИС: {name} - ок")
                else:
                    print(f"⚠️ 2ГИС: {name} - пусто. API врет!")
                    # Вызываем браузер для скриншота!
                    take_2gis_screenshot(firm_id, name)
            else:
                print(f"⚠️ 2ГИС: {name} ошибка {r.status_code}")
        except Exception as e: 
            print(f"❌ 2ГИС ошибка на {name}: {e}")
            continue
    
    if all_gis:
        all_gis.sort(key=lambda x: x["date"], reverse=True)
        for item in all_gis[:2]:
            item.pop("date", None)
            data["gis"].append(item)
    else:
        data["gis"] = [{"author": "Система", "location": "2ГИС", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Обновление 2ГИС временно недоступно."}]

    # 2. ЯНДЕКС (остается без изменений, он работает идеально)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 1200},
            locale="ru-RU"
        )
        page = context.new_page()
        try:
            print("Заходим на Яндекс (ул. Кирова)...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
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

            extracted = page.evaluate("""() => {
                let results = [];
                let cards = document.querySelectorAll('.business-review-view, .business-reviews-card-view__review');
                for (let i = 0; i < Math.min(5, cards.length); i++) {
                    let card = cards[i];
                    let authorEl = card.querySelector('.business-review-view__author-name') || card.querySelector('[itemprop="name"]');
                    let author = authorEl ? authorEl.innerText.trim() : "Клиент";
                    
                    let textEl = card.querySelector('[itemprop="reviewBody"]') || 
                                 card.querySelector('.business-review-view__body-text') || 
                                 card.querySelector('.business-review-view__text') || 
                                 card.querySelector('.business-reviews-card-view__review-text');
                    let text = textEl ? textEl.innerText.trim() : "";
                    
                    if (!text) { text = card.innerText.replace(author, '').trim().substring(0, 350) + "..."; }
                    
                    let rating = "5";
                    let ratingMeta = card.querySelector('meta[itemprop="ratingValue"]');
                    if (ratingMeta) { 
                        rating = ratingMeta.getAttribute('content'); 
                    } else {
                        let stars = card.querySelectorAll('.business-rating-badge-view__star._filled').length;
                        if (stars > 0) rating = stars.toString();
                    }
                    
                    if (text.length > 5) { results.push({author, text, rating}); }
                }
                return results;
            }""")
            
            if extracted:
                seen_texts = set()
                for res in extracted:
                    if len(data["yandex"]) >= 2: break
                    clean_text = res['text'].replace('\n', ' ').strip()
                    if clean_text and clean_text not in seen_texts:
                        seen_texts.add(clean_text)
                        data["yandex"].append({
                            "author": res['author'],
                            "location": "ул. Кирова, 146",
                            "stars": get_stars_emoji(res['rating']),
                            "text": clean_text
                        })
            print(f"✅ Яндекс собран. Уникальных: {len(data['yandex'])}")
        except Exception as e:
            print(f"⚠️ Ошибка Яндекса: {e}")
            if not data["yandex"]:
                data["yandex"] = [{"author": "Система", "location": "Яндекс", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Яндекс временно недоступен."}]
        browser.close()

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"🚀 Файл tv_data.json обновлен в {update_time}!")

if __name__ == "__main__":
    run()
