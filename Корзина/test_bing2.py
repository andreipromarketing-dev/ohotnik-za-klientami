import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

def search_bing(query):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        results = []
        for a in soup.select('li.b_algo h2 a'):
            href = a.get('href')
            if href and 'http' in href and not any(x in href for x in ['bing.com', 'microsoft.com']):
                results.append(href)
        
        print(f"Найдено: {len(results)}")
        for r_link in results[:5]:
            print(f" - {r_link}")
            
    except Exception as e:
        print("Ошибка:", e)

search_bing("Крымский бриз Ялта официальный сайт")
