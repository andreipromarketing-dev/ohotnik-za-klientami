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

# ============================================================================
# УРОВЕНЬ 1: БЫСТРЫЙ ФИЛЬТР (до запроса) — блок-лист + паттерны
# ============================================================================

AGGREGATORS_BLOCKLIST = [
    # === АГРЕГАТОРЫ ОТЕЛЕЙ ===
    "ostrovok.ru", "vashotel.ru", "jsprav.ru", "101hotels.com", "booking.com",
    "travel.ru", "tonkosti.ru", "hotelline.ru", "hotels.ru", "tophotels.ru",
    "bronevik.com", "travelata.ru", "sletat.ru", "tury.ru", "mirkvartir.ru",
    "sutochno.ru", "airbnb.com", "expedia.com", "hotels.com", "kayak.com",
    "trivago.com", "tripadvisor", "komandirovka", "megotel", "travel.yandex",
    "smf.is-tour", "spravka-region", "crimea-otel", "otpusk.com",
    "domik.travel", "hotel.tutu.ru", "tropki.ru", "mirturbaz.ru",
    "vkrim.info", "privettur.ru",

    # === КАТАЛОГИ / СПРАВОЧНИКИ ===
    "2gis.ru", "2gis.me", "yandex.ru/maps", "yandex.ru/spr", "yandex.com/maps",
    "google.ru/maps", "google.com/maps", "maps.me",
    "zoon.ru", "yell.ru", "bft-spb.ru",
    "rubrikator.ru", "spr.ru", "euromed.ru", "meds.ru",
    "namba.kg", "massandra.ua",
    "cataloxy.ru", "kronvest.net", "cataloxy.com",
    "ruscatalog.org", "list-org.com", "rusprofile.ru", "orgpage.ru",
    "spark-interfax.ru", "saby.ru", "companies.rbc.ru",

    # === УСЛУГИ / МАРКЕТПЛЕЙСЫ ===
    "profi.ru", "profiru.ru", "youdo.com", "avito.ru/uslugi",
    "youla.ru", "irr.ru", "drom.ru", "auto.ru",
    "cian.ru", "domclick.ru",

    # === ОТЗЫВЫ / РЕЙТИНГИ ===
    "flamp.ru", "otzovik.com", "irecommend.ru", "otzyvy.pro",
    "medobzor.ru", "pravoved.ru", "9111.ru", "yurist-online.net",

    # === СОЦСЕТИ ===
    "facebook.com", "fb.com", "instagram.com",
    "twitter.com", "x.com", "tiktok.com",
    "pinterest.com", "reddit.com", "tumblr.com",
    "linkedin.com", "snapchat.com",
    "wa.me", "whatsapp.com", "viber.com",

    # === ЕДА / ДОСТАВКА ===
    "eda.yandex.ru", "deliveryclub.ru", "samokat.ru",

    # === ПРОЧИЕ ПОРТАЛЫ ===
    "gorod24.online", "simferopolya.ru", "horeca-servise.ru",
    "visitsimferopol.ru", "bizly.ru", "2rus.org", "kudanamore.ru",
    "travelandia.ru", "rabotniki.ua", "remontexpress.ru",
    "stroikaspb.com", "spravker.ru", "etagi.com",
    "novograddom.ru", "dom-pod-klych.ru", "buildsim.ru",
    "365rem.ru", "proff-remont.ru",
    "prodoctorov.ru", "docdoc.ru", "napopravku.ru", "prontohelp.ru",
    "auto.yandex.ru", "aviasales.ru", "skyscanner.ru",
    "kupibilet.ru", "poezd.ru", "rasp.yandex.ru",
    "topface.ru", "megapersonals.ru", "mamba.ru", "loveplanet.ru",
    "dating.ru", "spravochnik.yandex.ru", "org.yandex.ru",
    "xn--p1ai", "xn--p1acf", "xn----7sbbagd1kffcl.xn--p1ai", "xn--80aflfte6clje.xn--p1ai",
    "sberbank.ru", "tinkoff.ru",
]

# Паттерны URL, которые ГАРАНТИРОВАННО указывают на каталог/агрегатор
AGGREGATOR_URL_PATTERNS = [
    r'/firm[si]/', r'/company/', r'/org/', r'/profile/',
    r'/catalog/', r'/catalogue/', r'/directory/',
    r'/city/', r'/hotels/', r'/tourism', r'/oteli-',
    r'/gostinitsy', r'/gostinitsi', r'/firmi',
    r'/medical/', r'/holiday_house/', r'/type/', r'/category/',
    r'/business/', r'/spravka/', r'/dost/', r'/uslug',
    r'/novostrojki/', r'/zhk-', r'/newobject/', r'/complex/',
    r'/zastrojshhik/', r'/object/', r'/service/',
    r'/\d{5,}',        # Длинные числовые ID
    r'/id\d+',         # ID-страницы агрегаторов
    r'/reviews',       # Страница отзывов
    r'/rating',        # Рейтинг
    r'/map/',          # Карта
    r'/search\?',      # Поисковые страницы
    r'/result',        # Результаты поиска
    r'/list',          # Списки
    r'/all',           # Все записи
    r'/near',          # Рядом
]

# Паттерны title, которые ГАРАНТИРОВАННО указывают на агрегатор
AGGREGATOR_TITLE_PATTERNS = [
    r'^\d+\s',
    r'отзыв[ыа]?\s',
    r'рейтинг\s',
    r'лучш\w+\s',
    r'топ-\d+',
    r'список\s',
    r'каталог\s',
    r'справочник\s',
    r'\d+\s+компани',
    r'\d+\s+организаци',
    r'\d+\s+клиник',
    r'\d+\s+отелей',
    r'\d+\s+сало',
    r'\d+\s+ресторан',
    r'где\s+в\s',
    r'адрес[а]?\s+и\s+телефон',
    r'все\s+компани',
    r'поиск\s+компани',
    r'рейтинг\s+лучш',
]


def is_aggregator_fast(url, title=""):
    """УРОВЕНЬ 1: Быстрый фильтр по URL + title (без запросов к сайту)"""
    url_lower = url.lower() if url else ""
    title_lower = title.lower() if title else ""

    # 1) Блок-лист доменов
    for agg in AGGREGATORS_BLOCKLIST:
        if agg in url_lower or agg in title_lower:
            return True

    # 2) Punycode — только конкретные агрегаторы в блок-листе, не все кириллические домены

    # 3) Паттерны URL
    for pattern in AGGREGATOR_URL_PATTERNS:
        if re.search(pattern, url_lower):
            return True

    # 4) Длинный путь (>3 сегментов = подозрительно)
    path = url_lower.split("//")[-1] if "//" in url_lower else url_lower
    segments = [s for s in path.split("/") if s]
    if len(segments) > 3:
        return True

    # 5) Паттерны title
    for pattern in AGGREGATOR_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return True

    # 6) Типичные агрегаторные слова
    agg_words = [
        "отзыв", "рейтинг", "каталог", "справочник",
        "список компаний", "адреса и телефоны", "все компании",
        "поиск", "найти", "где найти", "лучшие", "топ-",
    ]
    for word in agg_words:
        if word in title_lower:
            return True

    # 7) Слишком короткий title
    if title and len(title.strip()) < 5:
        return True

    return False


# ============================================================================
# УРОВЕНЬ 2: POST-FETCH ВАЛИДАЦИЯ (после загрузки страницы)
# ============================================================================

# Тексты, которые появляются на страницах агрегаторов/каталогов
AGGREGATOR_BODY_SIGNALS = [
    "все компании", "все организации", "каталог компаний",
    "каталог организаций", "список компаний", "список организаций",
    "рейтинг компаний", "рейтинг организаций",
    "найдите компанию", "найдите организацию",
    "адреса и телефоны", "адреса и контакты",
    "отзывы о компании", "отзывы об организации",
    "оставить отзыв", "написать отзыв",
    "показать на карте", "посмотреть на карте",
    "все отзывы", "все жалобы",
    "задать вопрос юристу", "получить консультацию",
    "profi.ru", "profi.ru/", "профиру",
    "profi.ru —", "профи.ру",
]

# Тексты, которые появляются на оригинальных сайтах компаний
SINGLE_BUSINESS_SIGNALS = [
    "мы работаем", "наша компания", "наш сайт",
    "о нас", "о компании", "о нашем",
    "наши услуги", "наши специалисты",
    "график работы", "режим работы",
    "запись на приём", "записаться",
    "call-center", "колл-центр",
    "наш адрес", "наш телефон",
    "принимаем к оплате", "способы оплаты",
    "гарантия", "наши преимущества",
    "портфолио", "наши работы",
]


def is_aggregator_content(page_text, company_name=""):
    """
    УРОВЕНЬ 2: Валидация по контенту страницы.
    Возвращает (is_aggregator: bool, reason: str).

    Логика: агрегатор = страница с информацией о МНОГИХ компаниях.
    Оригинальный сайт = ОДНА компания.
    """
    if not page_text or len(page_text) < 100:
        return False, ""

    text_lower = page_text.lower()
    score = 0
    reasons = []

    # --- СИГНАЛЫ АГРЕГАТОРА ---

    # 1) Много разных телефонов (разные коды = разные компании)
    phones = re.findall(r'(?:\+7|8|7)[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}', page_text)
    if len(phones) > 5:
        score += 3
        reasons.append(f"много_телефонов({len(phones)})")
    elif len(phones) > 3:
        score += 1
        reasons.append(f"норм_телефонов({len(phones)})")

    # 2) Текстовые сигналы агрегатора
    agg_signal_count = sum(1 for signal in AGGREGATOR_BODY_SIGNALS if signal in text_lower)
    if agg_signal_count >= 3:
        score += 3
        reasons.append(f"агрегаторных_сигналов({agg_signal_count})")
    elif agg_signal_count >= 1:
        score += 1
        reasons.append(f"сигнал_агрегатора({agg_signal_count})")

    # 3) Рейтинг/отзывы виджеты
    rating_patterns = [
        r'\d[\.,]\d\s+из\s+5',          # "4.8 из 5"
        r'\d[\.,]\d\s+из\s+10',         # "8.5 из 10"
        r'рейтинг\s*[\d\.,]+',          # "рейтинг 4.8"
        r'\d+\s+отзыв',                  # "12 отзывов"
        r'\d+\s+оцен',                   # "45 оценок"
        r'★{3,}',                        # "★★★★★"
        r'☆{3,}',                        # "☆☆☆☆☆"
    ]
    for pat in rating_patterns:
        if re.search(pat, text_lower):
            score += 2
            reasons.append(f"рейтинг_виджет")
            break

    # 4) Много разных адресов (разные филиалы = каталог)
    address_patterns = re.findall(r'(?:ул\.|улица|пр\.|проспект|пер\.|переулок|буль\.|бульвар|д\.\s*\d+)', page_text)
    if len(set(address_patterns)) > 3:
        score += 2
        reasons.append(f"много_адресов({len(set(address_patterns))})")

    # 5) Слова-маркеры каталога в body
    catalog_markers = [
        "все результаты", "показать ещё", "показать все",
        "загрузить ещё", "ещё компании", "все организации",
        "фильтр", "сортировка", "по умолчанию",
        "найдено:", "результатов:", "показано",
    ]
    catalog_count = sum(1 for m in catalog_markers if m in text_lower)
    if catalog_count >= 2:
        score += 2
        reasons.append(f"каталог_маркеры({catalog_count})")

    # --- СИГНАЛЫ ОРИГИНАЛЬНОГО САЙТА ---
    single_signals = sum(1 for signal in SINGLE_BUSINESS_SIGNALS if signal in text_lower)
    if single_signals >= 3:
        score -= 3
        reasons.append(f"сигнал_компании({single_signals})")
    elif single_signals >= 1:
        score -= 1
        reasons.append(f"сигнал_компании({single_signals})")

    # 6) Имя компании出现在 тексте (одна компания = её имя на сайте)
    if company_name and len(company_name) > 3:
        name_parts = company_name.split()
        name_mentions = sum(1 for part in name_parts if part.lower() in text_lower and len(part) > 3)
        if name_mentions >= 2:
            score -= 2
            reasons.append(f"имя_компании({name_mentions})")

    is_agg = score >= 3
    return is_agg, "; ".join(reasons)


# ============================================================================
# SEARCH ENGINE
# ============================================================================

async def search_duckduckgo(query, limit=20, log_func=None):
    """Поиск через DuckDuckGo с фильтрацией агрегаторов"""
    log_msg = log_func or (lambda m: print(f"DEBUG: {m}"))
    log_msg(f"DuckDuckGo search for: {query}")

    items = []

    if DDGS_AVAILABLE:
        try:
            def sync_search():
                results = []
                with DDGS() as ddgs:
                    for i, r in enumerate(ddgs.text(query, max_results=limit * 3)):
                        if i >= limit * 3:
                            break
                        results.append(r)
                return results

            results = await asyncio.to_thread(sync_search)
            log_msg(f"DuckDuckGo (ddgs): {len(results)} результатов (до фильтрации)")

            blocked_count = 0
            for r in results:
                title = r.get("title", "")
                url = r.get("href", "")
                if title and len(title) > 2 and not is_aggregator_fast(url, title):
                    items.append({
                        "name": title.strip(),
                        "firm_id": "",
                        "region": "",
                        "phones": [],
                        "emails": [],
                        "websites": [url] if url.startswith("http") else [],
                        "links": [url],
                        "addr": "—"
                    })
                else:
                    blocked_count += 1
                if len(items) >= limit:
                    break

            log_msg(f"DuckDuckGo: {len(items)} сайтов прошли фильтр (заблокировано: {blocked_count})")
            return items

        except Exception as e:
            log_msg(f"DuckDuckGo (ddgs) error: {e}")

    # Fallback HTTP
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"

    try:
        resp = await asyncio.to_thread(requests.get, url, headers=headers, timeout=30)
        if resp.status_code == 200:
            html = resp.text
            links = re.findall(r'href="(https?://[^"]+)"[^>]*>\s*([^<]+)\s*</a>', html)
            for url, name in links[:limit * 3]:
                if name and len(name) > 3 and not name.startswith("http") and not is_aggregator_fast(url, name):
                    items.append({
                        "name": name.strip(),
                        "firm_id": "",
                        "region": "",
                        "phones": [],
                        "emails": [],
                        "websites": [url] if url.startswith("http") else [],
                        "links": [url],
                        "addr": "—"
                    })
                if len(items) >= limit:
                    break
    except Exception as e:
        log_msg(f"DuckDuckGo fallback error: {e}")

    log_msg(f"DuckDuckGo найдено: {len(items)} результатов")
    return items

async def search_searchapi(query, limit=20, log_func=None):
    """Поиск через SearchApi.io (если есть ключ)"""
    log_msg = log_func or (lambda m: print(f"DEBUG: {m}"))

    if not config.SEARCHAPI_API_KEY:
        log_msg("SearchApi Key missing - используем DuckDuckGo")
        return await search_duckduckgo(query, limit, log_func)

    known_regions = list(config.REGION_COORDS.keys())
    query_lower = query.lower()
    is_known = any(city.lower() in query_lower for city in known_regions)

    if not is_known:
        log_msg(f"Город не из Крыма - используем DuckDuckGo")
        return await search_duckduckgo(query, limit, log_func)

    log_msg(f"SearchApi запрос: {query}")

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
            log_msg(f"SearchApi ответ: {len(results)} результатов")
            items = []
            for res in results[:limit]:
                website = res.get("website", "")
                if website and not is_aggregator_fast(website, res.get("title", "")):
                    items.append({
                        "name": res.get("title", "—"),
                        "firm_id": res.get("place_id"),
                        "region": "",
                        "phones": [res.get("phone")] if res.get("phone") else [],
                        "emails": [],
                        "websites": [website],
                        "links": [res.get("link")],
                        "addr": res.get("address", "—")
                    })
                elif not website:
                    items.append({
                        "name": res.get("title", "—"),
                        "firm_id": res.get("place_id"),
                        "region": "",
                        "phones": [res.get("phone")] if res.get("phone") else [],
                        "emails": [],
                        "websites": [],
                        "links": [res.get("link")],
                        "addr": res.get("address", "—")
                    })
            return items
        else:
            log_msg(f"SearchApi error {resp.status_code}: {resp.text[:200]} - fallback")
            return await search_duckduckgo(query, limit, log_func)
    except Exception as e:
        log_msg(f"SearchApi exception: {e} - fallback to DuckDuckGo")
        return await search_duckduckgo(query, limit, log_func)

async def fetch_companies(query, limit=20, log_func=None):
    """Поиск компаний - основная функция"""
    log_msg = log_func or (lambda m: print(f"DEBUG: {m}"))
    return await search_searchapi(query, limit, log_msg)
