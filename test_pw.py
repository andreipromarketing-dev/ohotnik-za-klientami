import asyncio
import time
import urllib.parse
from playwright.async_api import async_playwright

async def fast_playwright_search(query):
    start = time.time()
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Блокируем загрузку картинок для сверхскорости
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
        
        print(f"[{time.time()-start:.2f}s] Переход в Bing...")
        await page.goto(url, timeout=10000, wait_until="domcontentloaded")
        
        results = []
        try:
            print(f"[{time.time()-start:.2f}s] Ожидание селектора...")
            # Ждем появления первой ссылки (безо всяких sleep)
            await page.wait_for_selector("li.b_algo h2 a", timeout=3000)
            links = await page.locator("li.b_algo h2 a").all()
            for link in links:
                href = await link.get_attribute('href')
                if href and 'http' in href and not any(x in href for x in ['bing', 'microsoft']):
                    results.append(href)
        except Exception as e:
            print(f"Ошибка ожидания: {e}")
            
        await browser.close()
        
        print(f"[{time.time()-start:.2f}s] ФИНАЛ. Найдено ссылок: {len(results)}")
        for r in results[:3]:
            print(" -", r)

asyncio.run(fast_playwright_search("Крымский бриз Ялта официальный сайт"))
