import os
import json
import random
import requests
from datetime import datetime, timedelta

TV_DATA_FILE = "tv_data.json"

# ID филиалов (те же, что мы нашли раньше)
LOCATIONS_2GIS = {
    "50 лет ВЛКСМ": "70000001045878325",
    "Кирова, 146": "70000001083938641",
    "Удмуртская, 304": "70000001028907150",
    "9 Января, 219а": "70000001093448913",
    "ТЦ КИТ": "70000001042302381",
    "Молодежная": "70000001031336495"
}

LOCATIONS_YANDEX = {
    "Кирова, 146": "215636523165",
    "50 лет ВЛКСМ": "1726053880",
    "Удмуртская": "1325176045",
    "9 Января": "170942637213",
    "ТЦ КИТ": "1759491799",
    "Молодежная": "1205315808"
}

def get_stars_emoji(val):
    try:
        count = int(float(str(val).replace(',', '.')))
        return "⭐️" * count
    except: return "⭐️⭐️⭐️⭐️⭐️"

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    print(f"[{update_time}] СТАРТ: Сбор через Shadow API...")
    
    data = {"yandex": [], "gis": [], "last_update": update_time}
    s = requests.Session()
    
    # Маскируемся под обычный браузер
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    })

    # --- СБОР 2ГИС ---
    print("Собираем 2ГИС...")
    for name, firm_id in LOCATIONS_2GIS.items():
        try:
            url = f"https://public-api.reviews.2gis.com/2.0/branches/{firm_id}/reviews"
            params = {
                "limit": 5, "is_advertiser": "false", "rated": "true",
                "sort_by": "date_edited", "key": "37c04fe6-a560-4549-b459-0ce83ce384f3", "locale": "ru_RU"
            }
            # БЕЗ ЭТОГО REFERER БУДЕТ 403 ОШИБКА
            r = s.get(url, params=params, headers={"Referer": "https://2gis.ru/"}, timeout=10)
            if r.status_code == 200:
                reviews = r.json().get("reviews", [])
                for rev in reviews[:2]:
                    txt = rev.get("text", "").replace("\n", " ").strip()
                    if len(txt) > 5:
                        data["gis"].append({
                            "author": rev["user"]["name"], "location": name,
                            "stars": get_stars_emoji(rev.get("rating", 5)), "text": txt
                        })
                print(f"✅ 2ГИС {name}")
        except: print(f"❌ 2ГИС {name}")

    # --- СБОР ЯНДЕКС ---
    print("Собираем Яндекс...")
    for name, org_id in LOCATIONS_YANDEX.items():
        try:
            # Стучимся в API виджета
            url = f"https://yandex.ru/maps-reviews-widget/v1/getReviews?orgId={org_id}&pageSize=5"
            r = s.get(url, headers={"Referer": "https://yandex.ru/"}, timeout=10)
            if r.status_code == 200:
                # Яндекс отдает JSON внутри поля data
                items = r.json().get("data", {}).get("reviews", [])
                for item in items[:2]:
                    txt = item.get("text", "").replace("\n", " ").strip()
                    if len(txt) > 5:
                        data["yandex"].append({
                            "author": item.get("author", {}).get("name", "Клиент"),
                            "location": name,
                            "stars": get_stars_emoji(item.get("rating", 5)),
                            "text": txt
                        })
                print(f"✅ Яндекс {name}")
        except: print(f"❌ Яндекс {name}")

    # Перемешиваем и сохраняем
    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])
    data["gis"] = data["gis"][:2]
    data["yandex"] = data["yandex"][:2]

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"🚀 Готово! Собрано: 2ГИС({len(data['gis'])}), Яндекс({len(data['yandex'])})")

if __name__ == "__main__":
    run()
