import requests
import time

url = "http://127.0.0.1:1234/v1/chat/completions"
payload = {
    "model": "qwen3.5-9b",
    "messages": [
        {"role": "user", "content": "Скажи слово 'Привет' по-русски."}
    ],
    "temperature": 0.1
}

print(f"Отправка тестового запроса к модели qwen3.5-9b...")
start = time.time()
try:
    r = requests.post(url, json=payload, timeout=30)
    print(f"Статус HTTP: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        reply = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f"Ответ ИИ (за {time.time()-start:.1f} сек): {reply}")
    else:
        print(f"Ошибка API: {r.text}")
except Exception as e:
    print(f"Ошибка сети: {e}")
