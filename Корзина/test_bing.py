import requests
import re
import urllib.parse
import time

def search_bing(query):
    print(f"Поиск в Bing: {query}")
    start = time.time()
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"Статус: {r.status_code}, Время: {time.time()-start:.2f} сек")
        
        # Парсим ссылки из h2 тегов (заголовки результатов)
        # В Bing ссылки обычно выглядят так: <h2><a href="URL"...
        links = re.findall(r'<h2[^>]*><a[^>]+href="(https?://[^"]+)"', r.text)
        
        results = []
        for l in links:
            if not any(x in l for x in ['bing.com', 'microsoft.com']):
                results.append(l)
        
        print(f"Найдено: {len(results)}")
        for r_link in results[:5]:
            print(f" - {r_link}")
            
    except Exception as e:
        print("Ошибка:", e)

search_bing("Крымский бриз Ялта официальный сайт")
