import asyncio
import time
import urllib.parse
from playwright.async_api import async_playwright

async def fast_ddg_search(query):
    start = time.time()
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
        
        print(f"[{time.time()-start:.2f}s] Переход в DuckDuckGo HTML...")
        await page.goto(url, timeout=10000)
        
        results = []
        try:
            print(f"[{time.time()-start:.2f}s] Ожидание селектора...")
            # В DDG HTML ссылки имеют класс result__url
            await page.wait_for_selector("a.result__url", timeout=3000)
            links = await page.locator("a.result__url").all()
            for link in links:
                href = await link.get_attribute('href')
                if href and 'http' in href:
                    # decode redirect
                    if "/l/?kh=" in href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        href = parsed.get('uddg', [href])[0]
                    results.append(href)
        except Exception as e:
            print(f"Ошибка ожидания: {e}")
            
        await browser.close()
        
        print(f"[{time.time()-start:.2f}s] ФИНАЛ. Найдено ссылок: {len(results)}")
        for r in results[:3]:
            print(" -", r)

asyncio.run(fast_ddg_search("Крымский бриз Ялта официальный сайт"))
