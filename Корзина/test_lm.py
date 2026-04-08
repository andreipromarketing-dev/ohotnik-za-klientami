import requests

print("Тестируем подключение к LM Studio...")
url_models = "http://127.0.0.1:1234/v1/models"
try:
    r = requests.get(url_models, timeout=5)
    print(f"Статус: {r.status_code}")
    print(f"Ответ: {r.text[:500]}")
    
    data = r.json()
    models = data.get('data', [])
    if models:
        print(f"Загруженная модель: {models[0]['id']}")
    else:
        print("Список моделей пуст!")
except Exception as e:
    print(f"Ошибка подключения: {e}")
