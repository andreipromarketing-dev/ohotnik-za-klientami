import asyncio
import re
import urllib.parse
import aiohttp
import config
from playwright.async_api import async_playwright

try:
    from lm_studio_client import analyze_page_with_ai as ai_analyze, check_lm_studio as check_ai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    check_ai = lambda: False

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'(?:\+7|8|7)[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{1,3}[\s\-]?\d{2}[\s\-]?\d{2}'


async def search_website(company_name, log_func=None):
    """Ищет сайт компании через SearchApi"""
    if not company_name or not config.SEARCHAPI_API_KEY:
        return None
    
    try:
        import requests
        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "engine": "google",
            "q": f"{company_name} официальный сайт",
            "api_key": config.SEARCHAPI_API_KEY
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            organic = data.get("organic_results", [])
            for result in organic[:3]:
                link = result.get("link", "")
                if link and not any(x in link for x in ["youtube", "vk.com", "facebook", "instagram", "tilda"]):
                    return link
    except:
        pass
    return None


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
    except:
        pass
    return False

async def enrich_site_data(browser, url, company_name=None, log_func=None, use_ai=False):
    """Парсит сайт - извлекает контакты и соцсети"""
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
            if log_func: log_func(f"🚫 ЛПР не найден - пропуск")
            return res
        if log_func: log_func(f"✅ ЛПР обнаружен - парсинг...")

    html, text = "", ""
    context = None
    try:
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
        
        if log_func: log_func(f"🕸️ {url[:45]}...")
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(1.5)
        
        text = await page.evaluate("() => document.body.innerText")
        html = await page.content()
        await context.close()
    except Exception as e:
        if log_func: log_func(f"⚠️ {str(e)[:40]}")
        if context: await context.close()
        return res

    if text or html:
        phones = re.findall(PHONE_REGEX, text)
        emails = list(set(re.findall(EMAIL_REGEX, text + " " + html)))
        emails = [e for e in emails if not any(x in e.lower() for x in ['.png', '.jpg', 'sentry'])]
        emails = [e for e in emails if not re.match(r'^[\d\s\+\-\(\)]+$', e)]
        
        res['phones'] = phones[0] if phones else '—'
        res['emails'] = emails

        vk_links = re.findall(r'vk\.com\/[a-zA-Z0-9_.]+', html + text)
        tg_links = re.findall(r't\.me\/[a-zA-Z0-9_]+', html + text)
        
        vk_links = [l for l in vk_links if not any(x in l for x in ['share', 'like', 'comment', 'friend', 'acl', 'settings', 'feed', 'news'])]
        tg_links = [l for l in tg_links if len(l) > 6]
        
        if vk_links and res['VK'] == '—': 
            res['VK'] = f"https://{vk_links[0]}"
        if tg_links and res['TG'] == '—': 
            res['TG'] = f"https://{tg_links[0]}"
        
        max_links = re.findall(r'max\.ru', html)
        if max_links: res['MAX'] = f"https://{max_links[0]}"

        if use_ai and AI_AVAILABLE and check_ai():
            if log_func: log_func(f"🤖 AI...")
            ai_result = await ai_analyze(text, company_name)
            
            if ai_result.get('ai_success'):
                ai_people = ai_result.get('ai_people', [])
                if ai_people:
                    owners = [p for p in ai_people if p.get('type') in ['owner', 'director']]
                    if owners:
                        o = owners[0]
                        res['ЛПР'] = f"{o.get('name', '')} ({o.get('position', '')})"
                    elif ai_people:
                        p = ai_people[0]
                        res['ЛПР'] = f"{p.get('name', '')} ({p.get('position', '')})"
                    if log_func: log_func(f"   👤 {len(ai_people)} контактов")

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
            except: pass

    return res


async def batch_process(items_list, log_func=None, use_ai=False):
    """Параллельный парсинг сайтов"""
    semaphore = asyncio.Semaphore(7)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        async def sem_enrich(item):
            async with semaphore:
                site = (item.get('websites') or [None])[0]
                res = await enrich_site_data(browser, site, item.get('name'), log_func=log_func, use_ai=use_ai)
                
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
        
        tasks = [sem_enrich(item) for item in items_list]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result
        
        await browser.close()
