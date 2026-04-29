import os
import json
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

TV_DATA_FILE = "tv_data.json"
PROXY_URL = os.environ.get("MY_PROXY")

LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "https://2gis.ru/izhevsk/firm/70000001045878325/tab/reviews",
    "Кирова, 146": "https://2gis.ru/izhevsk/firm/70000001083938641/tab/reviews",
    "Удмуртская, 304": "https://2gis.ru/izhevsk/firm/70000001028907150/tab/reviews",
    "9 Января, 219а": "https://2gis.ru/izhevsk/firm/70000001093448913/tab/reviews",
    "ТЦ КИТ": "https://2gis.ru/izhevsk/firm/70000001042302381/tab/reviews",
    "Молодежная": "https://2gis.ru/izhevsk/firm/70000001031336495/tab/reviews"
}

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

def human_scroll(page):
    for i in range(random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(400, 800))
        page.wait_for_timeout(random.randint(1000, 2000))

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    print(f"[{update_time}] Сбор данных (Додо Пицца - ВСЕ ТОЧКИ)...")
    
    if PROXY_URL:
        print(f"🌐 Используем прокси: {PROXY_URL.split('@')[-1]}")
    else:
        print("⚠️ Прокси не задан, используем Stealth-маскировку Playwright")

    data = {"yandex": [], "gis": [], "last_update": update_time}

    with sync_playwright() as p:
        launch_args = {
            "headless": True,
            "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
        }
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}

        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768},
            locale="ru-RU"
        )
        page = context.new_page()
        
        # 🟢 МАГИЯ ТУТ: Накидываем маскировку на страницу до перехода на сайт
        stealth_sync(page)

        # --- ПАРСИМ 2ГИС ---
        for name, url in LOCATIONS_2GIS.items():
            try:
                print(f"2ГИС -> {name}...")
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000)
                human_scroll(page)
                
                res = page.evaluate("""() => {
                    let card = document.querySelector('article'); 
                    if (!card) return null;
                    let author = card.querySelector('header span:first-child')?.innerText.trim() || "Клиент";
                    let text = (card.querySelector('._j7emto') || card.querySelector('._192nvo0') || card.querySelector('._496d87'))?.innerText.trim() || "";
                    let rating = 5;
                    let stars = card.querySelector('._1f88pcy5') || card.querySelector('._1n8h0vx');
                    if (stars && stars.style.width) rating = Math.round(parseInt(stars.style.width) / 20);
                    return { author, text, rating };
                }""")
                
                if res and res['text']:
                    data["gis"].append({
                        "author": res['author'], "location": name,
                        "stars": get_stars_emoji(res['rating']), "text": res['text'].replace('\n', ' ')
                    })
                else:
                    page.screenshot(path=f"error_2gis_{name}.png")
            except Exception as e: 
                print(f"⚠️ Пропуск 2ГИС: {name}")

        # --- ПАРСИМ ЯНДЕКС ---
        for name, url in LOCATIONS_YANDEX.items():
            try:
                print(f"Яндекс -> {name}...")
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000)
                
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
                else:
                    page.screenshot(path=f"error_yandex_{name}.png")
            except Exception as e: 
                print(f"⚠️ Пропуск Яндекс: {name}")

        browser.close()

    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])

    data["gis"] = data["gis"][:2]
    data["yandex"] = data["yandex"][:2]

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"🚀 Готово! Собрано точек: 2ГИС({len(data['gis'])}), Яндекс({len(data['yandex'])})")

if __name__ == "__main__":
    run()
