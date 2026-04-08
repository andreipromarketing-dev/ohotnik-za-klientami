from googlesearch import search
import time

def test_gs():
    query = "гостевой дом Севастополь официальный сайт"
    start = time.time()
    try:
        # advanced=True вернет url, title, description
        res = list(search(query, num_results=5, lang="ru"))
        print(f"Готово за {time.time()-start:.2f} сек")
        for u in res:
            print(f" - {u}")
    except Exception as e:
        print(f"Ошибка Google: {e}")

test_gs()
