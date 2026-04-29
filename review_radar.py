import os
import json
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

TV_DATA_FILE = "tv_data.json"

# Прямые ссылки на отзывы для каждой точки
# --- ВСЕ 6 ТОЧЕК 2ГИС ---
LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "https://2gis.ru/izhevsk/firm/70000001045878325/tab/reviews",
    "Кирова, 146": "https://2gis.ru/izhevsk/firm/70000001083938641/tab/reviews",
    "Удмуртская, 304": "https://2gis.ru/izhevsk/firm/70000001028907150/tab/reviews",
    "9 Января, 219а": "https://2gis.ru/izhevsk/firm/70000001093448913/tab/reviews"
    "9 Января, 219а": "https://2gis.ru/izhevsk/firm/70000001093448913/tab/reviews",
    "ТЦ КИТ": "https://2gis.ru/izhevsk/firm/70000001042302381/tab/reviews", # Добавил точку в КИТе
    "Молодежная": "https://2gis.ru/izhevsk/firm/70000001031336495/tab/reviews"   # И шестую
}

# --- ВСЕ 6 ТОЧЕК ЯНДЕКСА ---
LOCATIONS_YANDEX = {
    "Кирова, 146": "https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/",
    "50 лет ВЛКСМ": "https://yandex.ru/maps/org/dodo_pitstsa/1726053880/reviews/",
    "Удмуртская": "https://yandex.ru/maps/org/dodo_pitstsa/1325176045/reviews/",
    "9 Января": "https://yandex.ru/maps/org/dodo_pitstsa/170942637213/reviews/",
    "ТЦ КИТ": "https://yandex.ru/maps/org/dodo_pitstsa/1759491799/reviews/",
    "Молодежная": "https://yandex.ru/maps/org/dodo_pitstsa/1205315808/reviews/"
}

def get_stars_emoji(val):
@@ -20,109 +33,84 @@ def get_stars_emoji(val):
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

def human_scroll(page):
    for i in range(random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(400, 800))
        page.wait_for_timeout(random.randint(1000, 2500))

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    print(f"[{update_time}] Сбор данных (Додо Пицца)...")
    print(f"[{update_time}] Сбор данных (Додо Пицца - ВСЕ ТОЧКИ)...")

    data = {"yandex": [], "gis": [], "last_update": update_time}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 1200},
            viewport={'width': 1366, 'height': 768},
            locale="ru-RU"
        )
        page = context.new_page()

        # --- БЛОК 2ГИС ---
        print("Собираем 2ГИС через браузер...")
        all_gis = []
        # --- ПАРСИМ 2ГИС (6 ресторанов) ---
        for name, url in LOCATIONS_2GIS.items():
            try:
                print(f"Заходим на 2ГИС: {name}...")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4000) # Ждем прогрузки списка
                print(f"2ГИС -> {name}...")
                page.goto(url, wait_until="networkidle", timeout=60000)
                human_scroll(page)

                # Парсим самый свежий отзыв на странице
                res = page.evaluate("""() => {
                    let card = document.querySelector('article'); 
                    if (!card) return null;
                    
                    let authorEl = card.querySelector('header span:first-child') || card.querySelector('._1695mnd');
                    let author = authorEl ? authorEl.innerText.trim() : "Клиент";
                    
                    let textEl = card.querySelector('._j7emto') || card.querySelector('._192nvo0') || card.querySelector('._496d87');
                    let text = textEl ? textEl.innerText.trim() : "";
                    
                    // Считаем звезды по количеству закрашенных элементов в блоке рейтинга
                    let author = card.querySelector('header span:first-child')?.innerText.trim() || "Клиент";
                    let text = (card.querySelector('._j7emto') || card.querySelector('._192nvo0'))?.innerText.trim() || "";
                    let rating = 5;
                    let starsContainer = card.querySelector('._1f88pcy5') || card.querySelector('._1n8h0vx');
                    if (starsContainer) {
                        let width = starsContainer.style.width; // Иногда рейтинг задается шириной блока
                        if (width) rating = Math.round(parseInt(width) / 20);
                    }
                    
                    let stars = card.querySelector('._1f88pcy5') || card.querySelector('._1n8h0vx');
                    if (stars && stars.style.width) rating = Math.round(parseInt(stars.style.width) / 20);
                    return { author, text, rating };
                }""")

                if res and res['text']:
                    all_gis.append({
                        "author": res['author'],
                        "location": name,
                        "stars": get_stars_emoji(res['rating']),
                        "text": res['text'].replace('\n', ' ')
                    data["gis"].append({
                        "author": res['author'], "location": name,
                        "stars": get_stars_emoji(res['rating']), "text": res['text'].replace('\n', ' ')
                    })
                    print(f"✅ {name}: отзыв получен")
            except Exception as e:
                print(f"⚠️ Ошибка на {name}: {e}")
                continue

        data["gis"] = all_gis[:2] # Берем только 2 свежих для ТВ
            except: print(f"⚠️ Пропуск 2ГИС: {name}")

        # --- БЛОК ЯНДЕКС ---
        try:
            print("Заходим на Яндекс (ул. Кирова)...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/215636523165/reviews/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            page.evaluate("""() => {
                let buttons = document.querySelectorAll('.business-review-view__body-expand, .business-review-view__expand');
                buttons.forEach(b => b.click());
            }""")
            page.wait_for_timeout(2000)

            extracted = page.evaluate("""() => {
                let results = [];
                let cards = document.querySelectorAll('.business-review-view');
                for (let card of cards) {
        # --- ПАРСИМ ЯНДЕКС (6 ресторанов) ---
        for name, url in LOCATIONS_YANDEX.items():
            try:
                print(f"Яндекс -> {name}...")
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(2000)
                
                res = page.evaluate("""() => {
                    let card = document.querySelector('.business-review-view');
                    if (!card) return null;
                    let author = card.querySelector('.business-review-view__author-name')?.innerText.trim() || "Клиент";
                    let text = card.querySelector('.business-review-view__body-text')?.innerText.trim() || "";
                    let stars = card.querySelectorAll('.business-rating-badge-view__star._filled').length || 5;
                    if (text.length > 10) results.push({author, text, rating: stars});
                }
                return results;
            }""")
            
            if extracted:
                for res in extracted[:2]:
                    return { author, text, rating: stars };
                }""")
                
                if res and res['text']:
                    data["yandex"].append({
                        "author": res['author'],
                        "location": "ул. Кирова, 146",
                        "stars": get_stars_emoji(res['rating']),
                        "text": res['text'].replace('\n', ' ')
                        "author": res['author'], "location": name,
                        "stars": get_stars_emoji(res['rating']), "text": res['text'].replace('\n', ' ')
                    })
            print(f"✅ Яндекс собран")
        except Exception as e:
            print(f"⚠️ Ошибка Яндекса: {e}")
            data["yandex"] = [{"author": "Система", "location": "Яндекс", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Яндекс временно недоступен."}]
            except: print(f"⚠️ Пропуск Яндекс: {name}")

        browser.close()

    # Перемешиваем отзывы, чтобы на ТВ каждый раз были разные точки
    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"🚀 Файл tv_data.json обновлен!")
    print(f"🚀 Готово! Собрано точек: 2ГИС({len(data['gis'])}), Яндекс({len(data['yandex'])})")

if __name__ == "__main__":
    run()
