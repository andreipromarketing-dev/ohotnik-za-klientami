import asyncio
from playwright.async_api import async_playwright
import enricher

async def test_enrich():
    print("🚀 Тест Глубокого поиска 3.0...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        res = await enricher.enrich_site_data(
            browser, 
            url=None, # Эмуляция ситуации, когда API не вернул сайт
            company_name="Крымский бриз", 
            city="Ялта", 
            log_func=print, 
            model_name="local-model"
        )
        print("=== ФИНАЛЬНЫЙ РЕЗУЛЬТАТ ===")
        print(res)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_enrich())
