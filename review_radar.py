import os
import json
import hashlib
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- ФАЙЛЫ ---
TV_DATA_FILE = "tv_data.json"

def get_stars(rating):
    try:
        r = int(float(str(rating)))
        return "⭐️" * r
    except:
        return "⭐️⭐️⭐️⭐️⭐️"

def run():
    print(f"[{datetime.now()}] Запуск облачного парсера...")
    
    # ТЕСТОВЫЕ ДАННЫЕ (чтобы телек ожил сразу, если парсинг не удастся)
    data = {
        "yandex": [{"author": "Система", "location": "Ижевск", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Поиск отзывов Яндекс..."}],
        "gis": [{"author": "Система", "location": "Ижевск", "stars": "⭐️⭐️⭐️⭐️⭐️", "text": "Поиск отзывов 2ГИС..."}]
    }

    with sync_playwright() as p:
        # Запуск в headless режиме (без окна) - КРИТИЧНО ДЛЯ GITHUB
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()

        try:
            # ПРИМЕР: ПАРСИНГ ОДНОЙ ТОЧКИ ЯНДЕКСА (замени URL на свой)
            print("Проверяем Яндекс...")
            page.goto("https://yandex.ru/maps/org/dodo_pitstsa/50127051254/reviews/", timeout=60000)
            page.wait_for_selector(".business-review-view__body-text", timeout=15000)
            
            review_text = page.locator(".business-review-view__body-text").first.inner_text()
            author = page.locator(".business-review-view__author-name").first.inner_text()
            
            data["yandex"][0] = {
                "author": author,
                "location": "50 лет ВЛКСМ",
                "stars": "⭐️⭐️⭐️⭐️⭐️",
                "text": review_text[:200] + "..."
            }
            print("✅ Яндекс найден!")

        except Exception as e:
            print(f"⚠️ Яндекс не поддался: {e}")

        browser.close()

    # ФИНАЛЬНЫЙ ШАГ: ЗАПИСЬ ФАЙЛА
    print(f"Записываем данные в {TV_DATA_FILE}...")
    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("🚀 ВСЁ! Скрипт завершен корректно.")

if __name__ == "__main__":
    run()
