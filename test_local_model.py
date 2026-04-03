import requests

url = "http://127.0.0.1:1234/v1/chat/completions"
payload = {
    "model": "local-model",
    "messages": [
        {"role": "user", "content": "Скажи Ок"}
    ],
    "temperature": 0.1
}
r = requests.post(url, json=payload, timeout=10)
print(f"Статус: {r.status_code}, Ответ: {r.text[:200]}")
