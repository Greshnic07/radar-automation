import os
import json
import random
import requests
import urllib.parse
from datetime import datetime, timedelta

TV_DATA_FILE = "tv_data.json"

# ВСТАВЬ СЮДА ССЫЛКУ, КОТОРУЮ ДАЛ ГУГЛ
GOOGLE_PROXY = "ТВОЯ_ССЫЛКА_ОТ_ГУГЛА"

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

def get_stars(val):
    return "⭐️" * int(float(str(val).replace(',', '.'))) if val else "⭐️⭐️⭐️⭐️⭐️"

def run():
    now = datetime.now() + timedelta(hours=4)
    update_time = now.strftime("%H:%M")
    print(f"[{update_time}] СТАРТ: Сбор через Google-пробойник...")
    
    data = {"yandex": [], "gis": [], "last_update": update_time}

    # --- 2ГИС ---
    for name, f_id in LOCATIONS_2GIS.items():
        try:
            target = f"https://public-api.reviews.2gis.com/2.0/branches/{f_id}/reviews?limit=3&key=37c04fe6-a560-4549-b459-0ce83ce384f3&locale=ru_RU"
            r = requests.get(f"{GOOGLE_PROXY}?url={urllib.parse.quote(target)}", timeout=20)
            if r.status_code == 200 and '"reviews"' in r.text:
                res = r.json()
                for rev in res.get("reviews", [])[:2]:
                    data["gis"].append({
                        "author": rev["user"]["name"], "location": name,
                        "stars": get_stars(rev.get("rating", 5)), "text": rev.get("text", "").replace("\n", " ")
                    })
                print(f"✅ 2ГИС {name}")
        except: print(f"❌ 2ГИС {name}")

    # --- ЯНДЕКС ---
    for name, org_id in LOCATIONS_YANDEX.items():
        try:
            target = f"https://yandex.ru/maps-reviews-widget/v1/getReviews?orgId={org_id}&pageSize=5"
            r = requests.get(f"{GOOGLE_PROXY}?url={urllib.parse.quote(target)}", timeout=20)
            if r.status_code == 200 and '"reviews"' in r.text:
                res = r.json()
                for rev in res.get("data", {}).get("reviews", [])[:2]:
                    data["yandex"].append({
                        "author": rev.get("author", {}).get("name", "Клиент"), "location": name,
                        "stars": get_stars(rev.get("rating", 5)), "text": rev.get("text", "").replace("\n", " ")
                    })
                print(f"✅ Яндекс {name}")
        except: print(f"❌ Яндекс {name}")

    random.shuffle(data["gis"])
    random.shuffle(data["yandex"])
    data["gis"] = data["gis"][:2]
    data["yandex"] = data["yandex"][:2]

    with open(TV_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"🚀 ИТОГ: Собрано {len(data['gis'])+len(data['yandex'])} отзывов.")

if __name__ == "__main__":
    run()
