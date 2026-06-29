import asyncio
import html as html_module
import json
import random
import re
import urllib.parse
import aiohttp
import config
from pathlib import Path
from playwright.async_api import async_playwright
from search_providers import AGGREGATOR_BODY_SIGNALS, SINGLE_BUSINESS_SIGNALS

CHECKPOINT_DIR = Path.home() / ".ohotnik"
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"


def save_checkpoint(results, processed_urls, search_params):
    """Сохраняет промежуточные результаты на диск"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "results": results,
        "processed_urls": list(processed_urls),
        "search_params": search_params,
        "raw_items": search_params.get("raw_items", []),
    }
    CHECKPOINT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_checkpoint():
    """Загружает чекпоинт. Возвращает (results, processed_urls, search_params, raw_items) или None"""
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return (
            data.get("results", []),
            set(data.get("processed_urls", [])),
            data.get("search_params", {}),
            data.get("raw_items", []),
        )
    except (json.JSONDecodeError, KeyError):
        return None


def delete_checkpoint():
    """Удаляет чекпоинт после успешного завершения"""
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

try:
    from lm_studio_client import analyze_page_with_ai as ai_analyze_lm, check_lm_studio as check_ai_lm, get_available_models as get_lm_models
    from groq_client import analyze_page_with_ai as ai_analyze_groq, check_groq as check_ai_groq, get_available_models as get_groq_models
    from unclose_client import analyze_page_with_ai as ai_analyze_unclose, check_unclose as check_ai_unclose, get_available_models as get_unclose_models
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    check_ai_lm = lambda: False
    check_ai_groq = lambda: False
    check_ai_unclose = lambda: False
    ai_analyze_lm = None
    ai_analyze_groq = None
    ai_analyze_unclose = None
    get_lm_models = lambda: []
    get_groq_models = lambda: {}
    get_unclose_models = lambda: {}

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:\+7|8|7)[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}'

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import extruct
    EXTRUCT_AVAILABLE = True
except ImportError:
    EXTRUCT_AVAILABLE = False


async def search_website(company_name, log_func=None):
    """Ищет сайт компании через SearchApi"""
    if not company_name or not config.SEARCHAPI_API_KEY:
        return None
    
    try:
        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "engine": "google",
            "q": f"{company_name} официальный сайт",
            "api_key": config.SEARCHAPI_API_KEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    organic = data.get("organic_results", [])
                    for result in organic[:3]:
                        link = result.get("link", "")
                        if link and not any(x in link for x in ["youtube", "facebook", "instagram", "tilda"]):
                            return link
    except Exception:
        pass
    return None


def _extract_from_html(html_text):
    """Извлекает контакты из HTML через href и plain text"""
    if not BS4_AVAILABLE:
        return {"emails": [], "vk_links": [], "tg_links": []}
    
    soup = BeautifulSoup(html_text, 'html.parser')
    emails = []
    vk_links = []
    tg_links = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        href_lower = href.lower()
        
        if href_lower.startswith('mailto:'):
            email = href.replace('mailto:', '').split('?')[0]
            from urllib.parse import unquote
            email = unquote(email)
            if '@' in email and '.' in email:
                emails.append(email.lower().strip())
        
        elif 'vk.com' in href_lower or 'm.vk.com' in href_lower or 'vk.cc' in href_lower:
            vk_links.append(href)
        
        elif 't.me/' in href_lower or 'telegram.me/' in href_lower:
            tg_links.append(href)
    
    return {"emails": emails, "vk_links": vk_links, "tg_links": tg_links}


def _extract_from_jsonld(html_text):
    """Извлекает контакты из JSON-LD Schema.org"""
    if not (BS4_AVAILABLE and EXTRUCT_AVAILABLE):
        return {"emails": [], "phones": []}
    
    try:
        from w3lib.html import get_base_url
        data = extruct.extract(html_text, base_url=get_base_url(html_text, ''), syntaxes=['json-ld'], uniform=True)
        emails = []
        phones = []
        
        for item in data.get('json-ld', []):
            _flatten_jsonld(item, emails, phones)
        
        return {"emails": emails, "phones": phones}
    except Exception:
        return {"emails": [], "phones": []}


def _flatten_jsonld(obj, emails, phones):
    """Рекурсивно ищет email/telephone в JSON-LD"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ('email', 'telephone'):
                if k == 'email' and isinstance(v, str) and '@' in v:
                    emails.append(v.lower())
                elif k == 'telephone' and isinstance(v, str):
                    phones.append(v)
            else:
                _flatten_jsonld(v, emails, phones)
    elif isinstance(obj, list):
        for item in obj:
            _flatten_jsonld(item, emails, phones)


def _extract_from_meta(html_text):
    """Извлекает контакты из Open Graph и других meta tags"""
    if not BS4_AVAILABLE:
        return {"emails": []}
    
    soup = BeautifulSoup(html_text, 'html.parser')
    emails = []
    
    for meta in soup.find_all('meta'):
        content = meta.get('content', '')
        if content and '@' in content and '.' in content:
            found = re.findall(EMAIL_REGEX, content)
            emails.extend(found)
    
    return {"emails": emails}


LPR_INDICATORS = ["директор", "гендиректор", "генеральный директор", "управляющ", "руководител", "владелец", "owner", "учредител", "администратор", "бенефициар", "首", "ceo", "chief", "director", "owner", "founder", "соучредител"]

async def quick_check_lpr(url, log_func=None):
    """Быстрая проверка страницы на наличие ЛПР без полного парсинга"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    text_lower = text.lower()
                    for indicator in LPR_INDICATORS:
                        if indicator.lower() in text_lower:
                            return True
    except Exception:
        pass
    return False
CONTACT_PAGE_PATTERNS = [
    "/contacts", "/kontakty", "/contact", "/about", "/about-us",
    "/o-nas", "/o-kompanii", "/callback", "/obratnaya-svyaz",
    "/feedback", "/svyaz", "/napisat-nam",
]

SOCIAL_DOMAINS = {
    "vk.com": "VK", "m.vk.com": "VK", "vk.cc": "VK",
    "t.me": "TG", "telegram.me": "TG", "telegram.org": "TG",
    "instagram.com": "IG", "www.instagram.com": "IG",
    "facebook.com": "FB", "www.facebook.com": "FB",
    "youtube.com": "YT", "www.youtube.com": "YT",
    "ok.ru": "OK", "www.ok.ru": "OK",
    "max.ru": "MAX",
}

EMAIL_BLACKLIST = [
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    "sentry", "wixpress", "webpack", "example.com",
    "test.com", "localhost", "schema.org",
    "w3.org", "googleapis.com", "gstatic.com",
    "facebook.com", "twitter.com", "instagram.com",
    "sentry.io", "bugsnag.com",
]



async def _is_aggregator_page(page, company_name=None, log_func=None):
    """
    УРОВЕНЬ 2: Post-fetch проверка — одна компания на странице или много (агрегатор).
    Возвращает True если это агрегатор → нужно ПРОПУСТИТЬ.
    """
    try:
        text = await page.evaluate("() => document.body.innerText")
    except Exception:
        return False

    if not text or len(text) < 100:
        return False

    text_lower = text.lower()
    score = 0
    reasons = []

    # 1) Много разных телефонов (разные коды = разные компании)
    phones = re.findall(r'(?:\+7|8|7)[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}', text)
    unique_phones = set(p.replace(" ", "").replace("-", "").replace("(", "").replace(")", "") for p in phones)
    if len(unique_phones) > 6:
        score += 4
        reasons.append(f"много_телефонов({len(unique_phones)})")
    elif len(unique_phones) > 3:
        score += 2
        reasons.append(f"телефонов({len(unique_phones)})")

    # 2) Текстовые сигналы агрегатора
    agg_signal_count = sum(1 for signal in AGGREGATOR_BODY_SIGNALS if signal in text_lower)
    if agg_signal_count >= 3:
        score += 4
        reasons.append(f"агрегаторных_сигналов({agg_signal_count})")
    elif agg_signal_count >= 1:
        score += 2
        reasons.append(f"сигнал_агрегатора({agg_signal_count})")

    # 3) Рейтинг-виджеты
    rating_patterns = [
        r'\d[\.,]\d\s+из\s+5',
        r'рейтинг\s*[\d\.,]+',
        r'\d+\s+отзыв',
        r'\d+\s+оцен',
    ]
    for pat in rating_patterns:
        if re.search(pat, text_lower):
            score += 2
            reasons.append("рейтинг_виджет")
            break

    # 4) Много разных адресов
    address_patterns = re.findall(r'(?:ул\.|улица|пр\.|проспект|пер\.|переулок|буль\.|бульвар)', text)
    if len(address_patterns) > 4:
        score += 2
        reasons.append(f"много_адресов({len(address_patterns)})")

    # 5) Слова-маркеры каталога
    catalog_markers = [
        "показать ещё", "показать все", "загрузить ещё",
        "все компании", "все организации",
        "фильтр", "сортировка",
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

    # 6) Имя компании в тексте
    if company_name and len(company_name) > 3:
        name_parts = company_name.split()
        name_mentions = sum(1 for part in name_parts if part.lower() in text_lower and len(part) > 3)
        if name_mentions >= 2:
            score -= 2
            reasons.append(f"имя_компании({name_mentions})")

    if score >= 4:
        if log_func:
            log_func(f"🚫 АГРЕГАТОР (score={score}): {'; '.join(reasons)}")
        return True

    return False

async def _extract_contacts_from_page(page, log_func=None):
    """Извлекает контакты из одной страницы Playwright"""
    emails = set()
    phones = []
    vk_links = set()
    tg_links = set()
    social_links = {}

    try:
        text = await page.evaluate("() => document.body.innerText")
        html = await page.content()
    except Exception:
        return {"emails": [], "phones": [], "vk": [], "tg": [], "social": {}}

    html_decoded = html_module.unescape(html) if html else ""
    full_text = (text or "") + " " + html_decoded

    # === EMAIL ===
    # 1) Regex в HTML
    raw_emails = re.findall(EMAIL_REGEX, html_decoded)
    emails.update(e.lower().strip() for e in raw_emails)

    # 2) mailto: ссылки
    mailto_matches = re.findall(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html_decoded)
    emails.update(e.lower().strip() for e in mailto_matches)

    # 3) JSON-LD
    if BS4_AVAILABLE and html_decoded:
        try:
            jsonld = _extract_from_jsonld(html_decoded)
            emails.update(jsonld.get("emails", []))
            phones.extend(jsonld.get("phones", []))
        except Exception:
            pass

    # 4) Meta tags
    if BS4_AVAILABLE and html_decoded:
        try:
            meta = _extract_from_meta(html_decoded)
            emails.update(meta.get("emails", []))
        except Exception:
            pass

    # 5) Текст страницы — ищем email прямо в innerText
    text_emails = re.findall(EMAIL_REGEX, text or "")
    emails.update(e.lower().strip() for e in text_emails)

    # Фильтрация мусорных email
    emails = [e for e in emails
              if not any(bad in e for bad in EMAIL_BLACKLIST)
              and not re.match(r'^[\d\s\+\-\(\)]+$', e)
              and len(e) > 5
              and "." in e.split("@")[-1]]

    # === PHONES ===
    if not phones:
        phones = re.findall(PHONE_REGEX, text or "")
    if not phones:
        phones = re.findall(PHONE_REGEX, html_decoded)

    # === SOCIAL LINKS ===
    # 1) href ссылки
    href_pattern = re.findall(r'href=["\']([^"\']+)["\']', html_decoded)
    for href in href_pattern:
        href_lower = href.lower()
        for domain, key in SOCIAL_DOMAINS.items():
            if domain in href_lower:
                if key == "VK":
                    vk_links.add(href)
                elif key == "TG":
                    tg_links.add(href)
                else:
                    social_links[key] = href

    # 2) Regex в HTML+текст
    vk_regex = re.findall(r'(?:vk\.com|m\.vk\.com|vk\.cc)/[a-zA-Z0-9_.]+', full_text)
    for link in vk_regex:
        clean = link.split("?")[0].rstrip("/")
        vk_links.add(f"https://{clean}" if not link.startswith("http") else link)

    tg_regex = re.findall(r't\.me/[a-zA-Z0-9_+]+', full_text)
    for link in tg_regex:
        tg_links.add(link)

    # 3) @username упоминания в тексте (_potential_ Telegram)
    mentions = re.findall(r'@\w{4,}', text or "")
    skip_mentions = {'@telegram', '@github', '@twitter', '@instagram', '@facebook', '@youtube'}
    for m in mentions:
        if m.lower() not in skip_mentions:
            tg_links.add(f"https://t.me/{m.lstrip('@')}")

    # 4) Ссылки в footer/header — часто содержат соцсети
    if BS4_AVAILABLE and html_decoded:
        try:
            soup = BeautifulSoup(html_decoded, 'html.parser')
            for tag in soup.find_all(['footer', 'header', 'nav']):
                for a in tag.find_all('a', href=True):
                    href_lower = a['href'].lower()
                    for domain, key in SOCIAL_DOMAINS.items():
                        if domain in href_lower:
                            if key == "VK":
                                vk_links.add(a['href'])
                            elif key == "TG":
                                tg_links.add(a['href'])
                            else:
                                social_links[key] = a['href']
        except Exception:
            pass

    # 5) Script/json embedded social data
    vk_script = re.findall(r'vk\.com/([a-zA-Z0-9_.]+)', html_decoded)
    for slug in vk_script:
        if slug not in ('', 'dev', 'doc'):
            vk_links.add(f"https://vk.com/{slug}")

    tg_script = re.findall(r't\.me/([a-zA-Z0-9_+]+)', html_decoded)
    for slug in tg_script:
        tg_links.add(f"https://t.me/{slug}")

    # Фильтрация VK
    vk_links = {l for l in vk_links
                if not any(x in l.lower() for x in ['share', 'like', 'comment', 'friend', 'acl', 'settings', 'feed', 'news', 'write'])}

    return {
        "emails": list(emails),
        "phones": phones,
        "vk": list(vk_links),
        "tg": list(tg_links),
        "social": social_links,
    }


async def _try_contact_pages(base_url, browser, log_func=None):
    """Пробует зайти на /contacts, /about и т.д. для извлечения контактов"""
    from urllib.parse import urljoin
    all_emails = set()
    all_phones = []
    all_vk = set()
    all_tg = set()
    all_social = {}

    for pattern in CONTACT_PAGE_PATTERNS:
        try:
            contact_url = urljoin(base_url, pattern)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            page = await context.new_page()
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())

            try:
                resp = await page.goto(contact_url, timeout=8000, wait_until="domcontentloaded")
                if resp and resp.status < 400:
                    await asyncio.sleep(0.3)
                    data = await _extract_contacts_from_page(page, log_func)
                    all_emails.update(data["emails"])
                    all_phones.extend(data["phones"])
                    all_vk.update(data["vk"])
                    all_tg.update(data["tg"])
                    all_social.update(data["social"])
            except Exception:
                pass
            finally:
                try:
                    await context.close()
                except Exception:
                    pass
        except Exception:
            pass

    return {
        "emails": list(all_emails),
        "phones": all_phones,
        "vk": list(all_vk),
        "tg": list(all_tg),
        "social": all_social,
    }


async def enrich_site_data(browser, url, company_name=None, log_func=None, use_ai=False, ai_provider="LM Studio", ai_model=""):
    """Парсит сайт - извлекает контакты и соцсети. Обходит main + contact-страницы."""
    res = {
        'site': url or '—',
        'phones': '—',
        'emails': [],
        'VK': '—',
        'TG': '—',
        'MAX': '—',
        'ЛПР': '—'
    }

    if not url or "http" not in url:
        if log_func: log_func(f"🔍 Поиск сайта...")
        url = await search_website(company_name, log_func)
        if url:
            res['site'] = url
            if log_func: log_func(f"   Найден: {url[:50]}...")
        else:
            return res

    if use_ai:
        if log_func: log_func(f"🔍 Быстрая проверка ЛПР...")
        has_lpr = await quick_check_lpr(url, log_func)
        if not has_lpr:
            if log_func: log_func(f"⚠️ ЛПР не найден в HTML - продолжаем парсинг")
        else:
            if log_func: log_func(f"✅ ЛПР обнаружен в HTML")

    # === ШАГ 1: Парсим главную страницу ===
    all_emails = set()
    all_phones = []
    all_vk = set()
    all_tg = set()
    all_social = {}

    context = None
    try:
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())

        if log_func: log_func(f"🕸️ {url[:45]}...")
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # === УРОВЕНЬ 2: Post-fetch проверка на агрегатор ===
        if await _is_aggregator_page(page, company_name, log_func):
            if log_func: log_func(f"🚫 Пропуск агрегатора: {url[:45]}")
            res['site'] = '— АГРЕГАТОР —'
            return res

        main_data = await _extract_contacts_from_page(page, log_func)
        all_emails.update(main_data["emails"])
        all_phones.extend(main_data["phones"])
        all_vk.update(main_data["vk"])
        all_tg.update(main_data["tg"])
        all_social.update(main_data["social"])

    except Exception as e:
        if log_func: log_func(f"⚠️ {str(e)[:40]}")
    finally:
        try:
            if context:
                await context.close()
        except Exception:
            pass

    # === ШАГ 2: Пробуем contact-страницы если мало данных ===
    total_contacts = len(all_emails) + len(all_phones) + len(all_vk) + len(all_tg)
    if total_contacts < 2:
        if log_func: log_func(f"🔍 Мало данных ({total_contacts}) - пробуем contact-страницы...")
        contact_data = await _try_contact_pages(url, browser, log_func)
        all_emails.update(contact_data["emails"])
        all_phones.extend(contact_data["phones"])
        all_vk.update(contact_data["vk"])
        all_tg.update(contact_data["tg"])
        all_social.update(contact_data["social"])

    # === Собираем результат ===
    unique_phones = list(dict.fromkeys(all_phones))
    res['phones'] = ", ".join(unique_phones[:5]) if unique_phones else '—'
    res['emails'] = list(all_emails)

    if all_vk:
        vk_url = sorted(all_vk)[0]
        res['VK'] = vk_url if vk_url.startswith("http") else f"https://{vk_url}"
    if all_tg:
        tg_url = sorted(all_tg)[0]
        res['TG'] = tg_url if tg_url.startswith("http") else f"https://{tg_url}"
    if "IG" in all_social:
        pass  # Instagram не сохраняем отдельно
    if "MAX" in all_social:
        res['MAX'] = all_social["MAX"] if all_social["MAX"].startswith("http") else f"https://{all_social['MAX']}"
    elif "max.ru" in " ".join(all_vk + all_tg):
        res['MAX'] = "https://max.ru"

    # === ШАГ 3: AI анализ ===
    ai_result = None
    if use_ai and AI_AVAILABLE:
        # Собираем текст со всех загруженных страниц для AI
        combined_text = ""
        try:
            context2 = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            page2 = await context2.new_page()
            await page2.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
            await page2.goto(url, timeout=12000, wait_until="domcontentloaded")
            await asyncio.sleep(0.3)
            combined_text = await page2.evaluate("() => document.body.innerText")
            await context2.close()
        except Exception:
            pass

        use_lm = ai_provider == "LM Studio" and check_ai_lm()
        use_groq = ai_provider == "Groq" and check_ai_groq()
        use_unclose = ai_provider == "UncloseAI" and check_ai_unclose()

        if (use_lm or use_groq or use_unclose) and combined_text:
            if log_func: log_func(f"🤖 AI ({ai_provider})...")

            if use_lm:
                ai_result = await ai_analyze_lm(combined_text, company_name, ai_model)
            elif use_groq:
                ai_result = await ai_analyze_groq(combined_text, company_name, ai_model)
            else:
                ai_result = await ai_analyze_unclose(combined_text, company_name, ai_model)

        if ai_result and ai_result.get('ai_success'):
            ai_people = ai_result.get('ai_people', [])
            ai_emails_from_ai = ai_result.get('ai_emails', [])
            ai_vk = ai_result.get('vk', '')
            ai_telegram = ai_result.get('telegram', '')
            if ai_emails_from_ai:
                existing = list(res['emails']) if not isinstance(res['emails'], list) else res['emails']
                new_emails = list(ai_emails_from_ai) if not isinstance(ai_emails_from_ai, list) else ai_emails_from_ai
                res['emails'] = list(set(existing) | set(new_emails))
            if ai_vk and res['VK'] == '—':
                res['VK'] = ai_vk if ai_vk.startswith('http') else f"https://{ai_vk}"
            if ai_telegram and res['TG'] == '—':
                tg_username = ai_telegram.lstrip('@')
                res['TG'] = f"https://t.me/{tg_username}"
            if ai_people:
                owners = [p for p in ai_people if p.get('type') in ['owner', 'director']]
                if owners:
                    o = owners[0]
                    res['ЛПР'] = f"{o.get('name', '')} ({o.get('position', '')})"
                elif ai_people:
                    p = ai_people[0]
                    res['ЛПР'] = f"{p.get('name', '')} ({p.get('position', '')})"
                if log_func: log_func(f"   👤 {len(ai_people)} контактов")

    # === ШАГ 4: VK API fallback ===
    async with aiohttp.ClientSession() as session:
        if config.VK_TOKEN and company_name:
            try:
                if res['VK'] == '—':
                    vk_url = f"https://api.vk.com/method/groups.search?q={urllib.parse.quote(company_name)}&access_token={config.VK_TOKEN}&v=5.131"
                    async with session.get(vk_url) as r:
                        vdata = await r.json()
                        groups = vdata.get('response', {}).get('items', [])
                        if groups:
                            g = groups[0]
                            club_id = g.get('id', '')
                            screen = g.get('screen_name', f'club{club_id}')
                            res['VK'] = f"https://vk.com/{screen}"

                if res['VK'] == '—':
                    search_name = company_name.split()[0]
                    vk_url = f"https://api.vk.com/method/users.search?q={urllib.parse.quote(search_name)}&access_token={config.VK_TOKEN}&v=5.131"
                    async with session.get(vk_url) as r:
                        vdata = await r.json()
                        users = vdata.get('response', {}).get('items', [])
                        if users and users[0].get('id'):
                            res['VK'] = f"https://vk.com/id{users[0].get('id')}"
            except Exception: pass

    return res


async def batch_process(items_list, log_func=None, use_ai=False, ai_provider="LM Studio", ai_model="",
                        processed_urls=None, search_params=None, checkpoint_every=20):
    """Параллельный парсинг сайтов с автосохранением"""
    semaphore = asyncio.Semaphore(4)
    skip_urls = processed_urls or set()
    results_so_far = []
    search_params = search_params or {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel='chrome')

        async def sem_enrich(item):
            async with semaphore:
                site = (item.get('websites') or [None])[0]
                try:
                    res = await enrich_site_data(browser, site, item.get('name'), log_func=log_func, use_ai=use_ai, ai_provider=ai_provider, ai_model=ai_model)
                except Exception as e:
                    if log_func: log_func(f"❌ Ошибка на {site or '—'}: {str(e)[:50]}")
                    res = {
                        'site': site or '—',
                        'phones': '—',
                        'emails': [],
                        'VK': '—',
                        'TG': '—',
                        'MAX': '—',
                        'ЛПР': '—'
                    }

                emails = res.get('emails', [])
                return {
                    "Компания": item.get('name', '—'),
                    "ЛПР": res.get("ЛПР", "—"),
                    "Телефон": res.get("phones", "—"),
                    "Email": ", ".join(emails[:3]) if emails else "—",
                    "Сайт": res.get("site", "—"),
                    "VK": res.get("VK", "—"),
                    "TG": res.get("TG", "—"),
                    "MAX": res.get("MAX", "—"),
                    "Адрес": item.get('addr', '—'),
                }

        # Фильтруем уже обработанные
        remaining = []
        for item in items_list:
            site = (item.get('websites') or [None])[0]
            if site and site in skip_urls:
                continue
            remaining.append(item)

        if skip_urls and log_func:
            log_func(f"⏩ Пропускаем {len(skip_urls)} уже обработанных, осталось {len(remaining)}")

        tasks = [sem_enrich(item) for item in remaining]
        count = 0
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                count += 1
                results_so_far.append(result)
                # Автосохранение каждые N результатов
                if count % checkpoint_every == 0:
                    all_urls = skip_urls | {r.get("Сайт", "") for r in results_so_far if r.get("Сайт", "") != "—"}
                    save_checkpoint(results_so_far, all_urls, search_params)
                    if log_func: log_func(f"💾 Чекпоинт сохранён ({count} обработано)")
                yield result
            except Exception as e:
                if log_func: log_func(f"❌ Task error: {str(e)[:50]}")
                continue

        # Финальное сохранение
        all_urls = skip_urls | {r.get("Сайт", "") for r in results_so_far if r.get("Сайт", "") != "—"}
        save_checkpoint(results_so_far, all_urls, search_params)

        try:
            await browser.close()
        except Exception:
            pass
