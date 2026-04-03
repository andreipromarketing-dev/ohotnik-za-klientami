import requests
import time

instances = [
    "https://searx.be/search",
    "https://searx.tiekoetter.com/search",
    "https://paulgo.io/search",
    "https://search.mdosch.de/search"
]

query = "гостевой дом Севастополь официальный сайт"

for url in instances:
    print(f"Тестируем: {url}...")
    start = time.time()
    try:
        r = requests.get(url, params={"q": query, "format": "json"}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            res = data.get("results", [])
            print(f"✅ Успех ({time.time()-start:.2f}с)! Найдено: {len(res)} ссылок.")
            for item in res[:2]:
                print(f"  - {item.get('url')}")
        else:
            print(f"⚠️ Ошибка {r.status_code}")
    except Exception as e:
        print(f"❌ Недоступен: {type(e).__name__}")
    print("-" * 30)
