from duckduckgo_search import DDGS

def test_search():
    query = "гостевой дом Севастополь официальный сайт"
    print(f"Поиск через DDGS API: {query}")
    try:
        results = DDGS().text(query, max_results=5)
        print(f"Найдено: {len(results)}")
        for r in results[:3]:
            print(f" - {r.get('title')}: {r.get('href')}")
    except Exception as e:
        print(f"Ошибка DDGS: {e}")

test_search()
