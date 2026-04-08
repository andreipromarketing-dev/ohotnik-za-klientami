import requests
import config
import asyncio
import re
from urllib.parse import quote_plus

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("DEBUG: ddgs not installed, falling back to basic search")

AGGREGATORS_BLOCKLIST = [
    "ostrovok.ru", "vashotel.ru", "jsprav.ru", "101hotels.com", "booking.com",
    "travel.ru", "tonkosti.ru", "hotelline.ru", "hotels.ru", "tophotels.ru",
    "bronevik.com", "travelata.ru", "sletat.ru", "tury.ru", "mirkvartir.ru",
    "gorod24.online", "simferopolya.ru", "horeca-servise.ru",
    "2gis.ru", "yandex.ru/maps", "google.ru/maps", "maps.me", "sutochno.ru",
    "airbnb.com", "expedia.com", "hotels.com", "kayak.com", "trivago.com",
    "tripadvisor", "komandirovka", "megotel", "travel.yandex", 
    "smf.is-tour", "spravka-region", "crimea-otel", "otpusk.com",
    "sberbank.ru", "tinkoff.ru",
    "zoon.ru", "visitsimferopol.ru", "spark-interfax.ru", "saby.ru",
    "vk.com/wall-",
    "cian.ru", "avito.ru", "youla.ru",
    "rusprofile.ru", "orgpage.ru", "rabotniki.ua", "remontexpress.ru",
    "stroikaspb.com", "drom.ru", "auto.ru", "irr.ru",
    "xn--p1ai", "xn--p1acf",
    "spravker.ru", "etagi.com", "cataloxy.ru", "kronvest.net",
    "365rem.ru", "proff-remont.ru", "ruscatalog.org", "novograddom.ru",
    "dom-pod-klych.ru", "buildsim.ru", "list-org.com", "domclick.ru",
    "bizly.ru", "2rus.org", "kudanamore.ru", "travelandia.ru",
    "domik.travel", "hotel.tutu.ru", "tropki.ru", "mirturbaz.ru",
    "vkrim.info", "companies.rbc.ru", "privettur.ru",
]

def is_aggregator(url, title=""):
    """Проверяет, является ли результат агрегатором или каталогом"""
    url_lower = url.lower() if url else ""
    title_lower = title.lower() if title else ""
    
    for agg in AGGREGATORS_BLOCKLIST:
        if agg in url_lower or agg in title_lower:
            return True
    
    if "xn--" in url_lower and ".ru" in url_lower:
        return True
    
    # Проверка глубины URL - слишком много сегментов = каталог/агрегатор
    path = url_lower.split("//")[-1] if "//" in url_lower else url_lower
    segments = path.split("/")
    # Если больше 4 сегментов - скорее всего каталог объектов
    if len([s for s in segments if s]) > 4:
        return True
    
    # Каталоговые пути агрегаторов
    catalog_path_patterns = [
        "/city/", "/hotels/", "/tourism", "/oteli-", "/gostinitsy", "/gostinitsi", 
        "/firmi", "/medical/", "/holiday_house/", "/type/", "/category/", 
        "/business/", "/catalog/", "/spravka/", "/dost/", "/uslug",
        "/novostrojki/", "/zhk-", "/newobject/", "/complex/", "/zastrojshhik/",
        "/ объектов", "/объект/", "/service/", "/каталог", "/catalog/",
        "/contact-us", "/contacts", "/about", "/produktsiya",
    ]
    for pattern in catalog_path_patterns:
        if pattern in url_lower:
            return True
    
    # Паттерны агрегаторов в URL (id объекта, код города и т.д.)
    aggregator_patterns = [
        r'/\d{4,}',  # много цифр подряд (id объектов)
        r'/id\d+',   # id в URL
        r'/club\d+', # vk club id
    ]
    for pattern in aggregator_patterns:
        if re.search(pattern, url_lower):
            return True
    
    has_number = any(c.isdigit() for c in title[:10])
    if has_number and any(w in title_lower for w in ["компани", "организаци", "предприят", "фирм"]):
        return True
    
    if title and len(title) < 5:
        return True
    
    return False

async def search_duckduckgo(query, limit=20):
    """Поиск через DuckDuckGo (безлимитно, бесплатно)"""
    print(f"DEBUG: DuckDuckGo search for: {query}")
    
    items = []
    
    if DDGS_AVAILABLE:
        try:
            def sync_search():
                results = []
                with DDGS() as ddgs:
                    search_query = f"{query} компании"
                    for i, r in enumerate(ddgs.text(search_query, max_results=limit)):
                        if i >= limit:
                            break
                        results.append(r)
                return results
            
            results = await asyncio.to_thread(sync_search)
            
            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")
                if title and len(title) > 2 and not is_aggregator(url, title):
                    items.append({
                        "name": title.strip(),
                        "firm_id": "",
                        "region": query.split()[-1] if len(query.split()) > 1 else "",
                        "phones": [],
                        "emails": [],
                        "websites": [url] if url.startswith("http") else [],
                        "links": [url],
                        "addr": "—"
                    })
            
            print(f"DEBUG: DuckDuckGo (ddgs) found {len(items)} results")
            return items
            
        except Exception as e:
            print(f"DEBUG: DuckDuckGo (ddgs) error: {e}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}+компании"
    
    try:
        resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=30)
        if resp.status_code == 200:
            html = resp.text
            links = re.findall(r'href="(https?://[^"]+)"[^>]*>\s*([^<]+)\s*</a>', html)
            for url, name in links[:limit]:
                if name and len(name) > 3 and not name.startswith("http") and not is_aggregator(url, name):
                    items.append({
                        "name": name.strip(),
                        "firm_id": "",
                        "region": query.split()[-1] if len(query.split()) > 1 else "",
                        "phones": [],
                        "emails": [],
                        "websites": [url] if url.startswith("http") else [],
                        "links": [url],
                        "addr": "—"
                    })
    except Exception as e:
        print(f"DEBUG: DuckDuckGo fallback error: {e}")
    
    print(f"DEBUG: DuckDuckGo found {len(items)} results")
    return items

async def search_searchapi(query, limit=20):
    """Поиск через SearchApi.io (если есть ключ)"""
    if not config.SEARCHAPI_API_KEY:
        print("DEBUG: SearchApi Key missing - using DuckDuckGo")
        return await search_duckduckgo(query, limit)
    
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": config.SEARCHAPI_API_KEY
    }
    
    try:
        resp = await asyncio.to_thread(requests.get, url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("local_results", [])
            print(f"DEBUG: SearchApi found {len(results)} results")
            items = []
            for res in results[:limit]:
                items.append({
                    "name": res.get("title", "—"),
                    "firm_id": res.get("place_id"),
                    "region": query.split()[-1],
                    "phones": [res.get("phone")] if res.get("phone") else [],
                    "emails": [],
                    "websites": [res.get("website")] if res.get("website") else [],
                    "links": [res.get("link")],
                    "addr": res.get("address", "—")
                })
            return items
        else:
            print(f"DEBUG: SearchApi Error {resp.status_code}: {resp.text} - falling back to DuckDuckGo")
            return await search_duckduckgo(query, limit)
    except Exception as e:
        print(f"DEBUG: SearchApi exception: {e} - falling back to DuckDuckGo")
        return await search_duckduckgo(query, limit)

async def fetch_companies(query, limit=20):
    """Поиск компаний - основная функция"""
    return await search_searchapi(query, limit)
