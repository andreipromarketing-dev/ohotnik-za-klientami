import requests
from bs4 import BeautifulSoup
import time

def search_ddg_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"q": query}
    
    start = time.time()
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        print(f"Статус: {r.status_code}, Время: {time.time()-start:.2f} сек")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            results = []
            for a in soup.select("a.result-snippet"):
                href = a.get('href')
                if href and 'http' in href:
                    results.append(href)
            
            for a in soup.select("td.result-snippet"):
                # sometimes links are inside
                pass
            
            # В lite ddg ссылки часто лежат в 'a.result-url'
            for a in soup.select("a.result-url"):
                href = a.get('href')
                if href and 'http' in href:
                    results.append(href)
                    
            print(f"Найдено ссылок: {len(results)}")
            for res in results[:3]:
                print(f" - {res}")
            return results
    except Exception as e:
        print(f"Ошибка: {e}")

search_ddg_lite("гостевой дом Севастополь официальный сайт")
