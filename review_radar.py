import os
import json
import random
import requests
import re
from datetime import datetime, timedelta

TV_DATA_FILE = "tv_data.json"

# Используем ID филиалов для прямого поиска на Flamp (это тот же 2ГИС)
LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913",
    "ТЦ КИТ": "70000001042302381",
    "Молодежная": "70000001031336495"
}

# ID для Яндекса
LOCATIONS_YANDEX = {
    "Кирова, 146": "215636523165",
    "50 лет ВЛКСМ": "1726053880",
    "Удмуртская": "1325176045",
    "9 Января": "170942637213",
    "ТЦ КИТ": "1759491799",
    "Молодежная": "1205315808"
}

def get_stars(val):
    return "⭐️" * int(float(str(val).replace(',', '.'))) if val else "⭐️⭐️⭐️⭐️⭐️"

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    print(f"[{update_time}] СТАРТ: Глубокий поиск...")
    
    data = {"yandex": [], "gis": [], "last_update": update_time}
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"})

    # --- 2ГИС через FLAMP (Обход защиты) ---
    print("--- Сбор 2ГИС (через Flamp) ---")
    for name, f_id in LOCATIONS_2GIS.items():
        try:
            # Flamp кушает те же ID, что и 2ГИС
            url = f"https://izhevsk.flamp.ru/firm/dodo_picca_set_piccerijj-{f_id}"
            r = s.get(url, timeout=15)
            print(f"-> {name}: Статус {r.status_code}")
            
            if r.status_code == 200:
                # Вытаскиваем отзывы через регулярку (самый быстрый способ)
                texts = re.findall(r'"text":"([^"]+)"', r.text)
                authors = re.findall(r'"name":"([^"]+)"', r.text)
                if texts:
                    data["gis"].append({
                        "author": authors[1] if len(authors)>1 else "Клиент",
                        "location": name,
                        "stars": "⭐️⭐️⭐️⭐️⭐️",
                        "text": texts[0][:150].replace('\\n', ' ')
                    })
                    print(f"   ✅ Нашли отзыв!")
        except Exception as e: print(f"   ❌ Ошибка: {e}")

    # --- ЯНДЕКС через Мобильный Виджет ---
    print("\n--- Сбор Яндекс (через Widget API) ---")
    for name, org_id in LOCATIONS_YANDEX.items():
        try:
            url = f"https://yandex.ru/maps-reviews-widget/v1/getReviews?orgId={org_id}&pageSize=5"
            r = s.get(url, headers={"Referer": "https://yandex.ru/"}, timeout=15)
            print(f"-> {name}: Статус {r.status_code}")
            
            if r.status_code == 200:
                res = r.json()
                reviews = res.get("data", {}).get("reviews", [])
                if reviews:
                    rev = reviews[0]
                    data["yandex"].append({
                        "author": rev.get("author", {}).get("name", "Клиент"),
                        "location": name,
                        "stars": get_stars(rev.get("rating", 5)),
                        "text": rev.get("text", "")[:150].replace('\n', ' ')
                    })
                    print(f"   ✅ Нашли отзыв!")
        except Exception as e: print(f"   ❌ Ошибка: {e}")

    # Финалим
    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])
    data["gis"] = data["gis"][:2]
    data["yandex"] = data["yandex"][:2]

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n🚀 ИТОГ: 2ГИС({len(data['gis'])}), Яндекс({len(data['yandex'])})")

if __name__ == "__main__":
    run()
