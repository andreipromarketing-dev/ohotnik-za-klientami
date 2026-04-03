import asyncio
import enricher

async def test_search():
    res = await enricher.find_website_fast("Крымский бриз", "Ялта", log_func=print)
    print("Результат find_website_fast:", res)

asyncio.run(test_search())
