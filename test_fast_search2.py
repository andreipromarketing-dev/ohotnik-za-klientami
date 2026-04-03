import urllib.request
import urllib.parse
import re
import time

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    start = time.time()
    try:
        response = urllib.request.urlopen(req, timeout=10)
        html = response.read().decode('utf-8')
        print(f"Статус: {response.status}, Время: {time.time()-start:.2f} сек")
        
        # Парсим ссылки вида href="http..."
        links = re.findall(r'href="(https?://[^"]+)"', html)
        results = [l for l in links if not any(x in l for x in ['duckduckgo', 'yandex', 'bing', 'vk.com'])]
        
        print(f"Найдено релевантных ссылок: {len(results)}")
        for res in results[:3]:
            print(f" - {res}")
        return results
    except Exception as e:
        print(f"Ошибка: {e}")

search_ddg_lite("гостевой дом Севастополь официальный сайт")
