from googlesearch import search

query = "Крымский бриз Ялта официальный сайт"
try:
    print("Testing basic search...")
    res = list(search(query, num_results=10, lang="ru"))
    print("Basic res:", res)
    
    print("Testing advanced search...")
    res2 = list(search(query, advanced=True, num_results=10, lang="ru"))
    print("Advanced res:", res2)
except Exception as e:
    print("Error:", e)
