#!/usr/bin/env python3
"""
Сбор НТО (киоски, павильоны, ларьки и т.п.) по области Якутска через 2ГИС Places API.
Ключ: https://dev.2gis.ru  (бесплатный демо-ключ).
Запуск:  pip install requests
         python nto_2gis.py ВАШ_КЛЮЧ
Результат: nto_avtodorozhny.csv
"""
import sys, csv, math, time
import requests

API_KEY = sys.argv[1] if len(sys.argv) > 1 else "ВСТАВЬТЕ_КЛЮЧ"

# --- ОБЛАСТЬ ПОИСКА -------------------------------------------------------
# Если знаете границы округа - задайте POLYGON (список (lon, lat) по кругу).
# Получить координаты: правый клик по карте 2ГИС -> «Что здесь?» / или geojson.io
# Если POLYGON пустой - используется прямоугольник BBOX.
# ВНИМАНИЕ: значения ниже ПРИМЕРНЫЕ - проверьте и поправьте под свой округ!
BBOX = (129.66, 62.00, 129.78, 62.06)   # (lon_min, lat_min, lon_max, lat_max)
POLYGON = []                            # например: [(129.68, 62.01), (129.75, 62.01), ...]

CELL_RADIUS_M = 400   # радиус одной ячейки сетки (меньше = полнее результат)

QUERIES = [
    "киоск", "павильон", "ларёк", "торговый павильон", "продукты",
    "цветы", "овощи фрукты", "хлеб", "выпечка", "шаурма", "кофе с собой",
    "мороженое", "табак", "аптека", "печать", "остановочный комплекс",
    "фастфуд", "мясо", "рыба", "магазин",
]
# --------------------------------------------------------------------------

URL = "https://catalog.api.2gis.com/3.0/items"
FIELDS = "items.point,items.address_name,items.contact_groups,items.rubrics,items.name_ex"


def in_polygon(lon, lat, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            if lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def grid_points():
    lon_min, lat_min, lon_max, lat_max = BBOX
    if POLYGON:
        lons = [p[0] for p in POLYGON]; lats = [p[1] for p in POLYGON]
        lon_min, lon_max, lat_min, lat_max = min(lons), max(lons), min(lats), max(lats)
    dlat = (CELL_RADIUS_M * 1.4) / 111_000
    dlon = dlat / math.cos(math.radians((lat_min + lat_max) / 2))
    lat = lat_min
    while lat <= lat_max:
        lon = lon_min
        while lon <= lon_max:
            yield lon, lat
            lon += dlon
        lat += dlat


def phones(item):
    out = []
    for g in item.get("contact_groups", []):
        for c in g.get("contacts", []):
            if c.get("type") == "phone":
                out.append(c.get("text") or c.get("value"))
    return "; ".join(dict.fromkeys(filter(None, out)))


def search(q, lon, lat):
    page = 1
    while page <= 10:
        r = requests.get(URL, params={
            "q": q, "point": f"{lon},{lat}", "radius": CELL_RADIUS_M,
            "type": "branch", "page": page, "page_size": 50,
            "fields": FIELDS, "locale": "ru_RU", "key": API_KEY,
        }, timeout=30)
        if r.status_code != 200:
            print("Ошибка", r.status_code, r.text[:200]); return
        data = r.json()
        items = data.get("result", {}).get("items", [])
        if not items:
            return
        yield from items
        if len(items) < 50:
            return
        page += 1
        time.sleep(0.1)


def main():
    found = {}
    points = list(grid_points())
    print(f"Ячеек: {len(points)}, запросов: {len(points) * len(QUERIES)}")
    for i, (lon, lat) in enumerate(points, 1):
        for q in QUERIES:
            for it in search(q, lon, lat):
                p = it.get("point")
                if not p:
                    continue
                if POLYGON and not in_polygon(p["lon"], p["lat"], POLYGON):
                    continue
                found[it["id"]] = {
                    "название": it.get("name", ""),
                    "адрес": it.get("address_name", ""),
                    "телефоны": phones(it),
                    "рубрики": ", ".join(r["name"] for r in it.get("rubrics", [])),
                    "lat": p["lat"], "lon": p["lon"],
                    "ссылка": f"https://2gis.ru/yakutsk/firm/{it['id'].split('_')[0]}",
                }
        print(f"{i}/{len(points)}  найдено: {len(found)}")

    with open("nto_avtodorozhny.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["название", "адрес", "телефоны", "рубрики", "lat", "lon", "ссылка"], delimiter=";")
        w.writeheader()
        w.writerows(sorted(found.values(), key=lambda x: x["адрес"]))
    print("Готово: nto_avtodorozhny.csv")


if __name__ == "__main__":
    main()
