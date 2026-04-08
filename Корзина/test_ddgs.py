from duckduckgo_search import AsyncDDGS
import asyncio
import time

async def test_search():
    query = "гостевой дом Севастополь официальный сайт"
    print(f"Поиск через DDGS API: {query}")
    start = time.time()
    
    try:
        # Использование асинхронного клиента
        async with AsyncDDGS() as ddgs:
            results = await asyncio.to_thread(lambda: list(ddgs.text(query, max_results=5)))
            
            print(f"Готово за {time.time()-start:.2f} сек!")
            print(f"Найдено: {len(results)}")
            for r in results[:3]:
                print(f" - {r.get('title')}: {r.get('href')}")
    except Exception as e:
        print(f"Ошибка DDGS: {e}")

asyncio.run(test_search())
