"""
OmniRoute AI Integration — для анализа страниц и извлечения контактов
"""
import os
import json
import aiohttp

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://localhost:20128")

EXTRACT_CONTACTS_PROMPT = """Ты парсер контактной информации с веб-страниц компаний.

Извлеки из текста страницы:
1. EMAIL - все email адреса (отделов, сотрудников, общие)
2. СОЦИАЛЬНЫЕ СЕТИ - ссылки на профили (LinkedIn, VK, Facebook, Instagram)
3. ЛПР - имена и должности людей (директор, CEO, owner, учредитель, менеджер)
4. СОБСТВЕННИКИ - информация о собственниках/учредителях бизнеса
5. КОНТАКТЫ - телефоны, адреса, формы обратной связи

Формат ответа строго JSON:
{
  "emails": ["email1@company.ru", "info@company.ru"],
  "socials": {"linkedin": "https://linkedin.com/...", "vk": "https://vk.com/...", "facebook": "..."},
  "people": [{"name": "Имя Фамилия", "position": "должность", "type": "owner|director|manager|contact"}],
  "contacts": {"phones": ["+7..."], "address": "адрес"},
  "confidence": 0.8
}

Если данных нет — возвращай пустые массивы/объекты. Не выдумывай информацию."""


async def call_omniroute(system_prompt: str, user_message: str, model: str = "lm-studio/qwen3.5-9b") -> dict:
    """Отправляет запрос к OmniRoute API. По умолчанию использует LM-Studio (локальный)."""
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 2000,
        "temperature": 0
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OMNIROUTE_URL}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    # Пытаемся извлечь JSON из ответа
                    try:
                        # Убираем markdown код блоки если есть
                        if "```json" in content:
                            content = content.split("```json")[1].split("```")[0]
                        elif "```" in content:
                            content = content.split("```")[1].split("```")[0]
                        return json.loads(content.strip())
                    except json.JSONDecodeError:
                        return {"error": "JSON parse failed", "raw": content[:500]}
                else:
                    error_text = await resp.text()
                    return {"error": f"API error {resp.status}: {error_text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


async def analyze_page_with_ai(page_text: str, company_name: str = "") -> dict:
    """Анализирует текст страницы и извлекает контактную информацию"""
    
    user_message = f"Компания: {company_name}\n\nТекст страницы:\n{page_text[:15000]}"
    
    result = await call_omniroute(EXTRACT_CONTACTS_PROMPT, user_message)
    
    if "error" not in result:
        return {
            "ai_emails": result.get("emails", []),
            "ai_socials": result.get("socials", {}),
            "ai_people": result.get("people", []),
            "ai_contacts": result.get("contacts", {}),
            "ai_confidence": result.get("confidence", 0),
            "ai_success": True
        }
    else:
        return {
            "ai_emails": [],
            "ai_socials": {},
            "ai_people": [],
            "ai_contacts": {},
            "ai_confidence": 0,
            "ai_success": False,
            "ai_error": result.get("error")
        }


def check_omniroute_connection() -> bool:
    """Проверяет доступность OmniRoute"""
    try:
        import requests
        resp = requests.get(f"{OMNIROUTE_URL}", timeout=5)
        return resp.status_code in [200, 307, 308]
    except:
        return False


def generate_personalized_email(company_name: str, person: dict, product: str = "чат-бот для записи") -> str:
    """Генерирует персонализированное КП для контакта"""
    
    prompt = f"""Напиши персонализированное коммерческое предложение на русском языке.

Компания: {company_name}
Контакт: {person.get('name', '')}, {person.get('position', '')}
Продукт: {product}

Требования:
- Краткое (3-4 предложения)
- Персонализированное (упомяни имя и компанию)
- Конкретное (что именно решит)
- Призыв к действию в конце

Формат: просто текст письма, без JSON."""

    import requests
    payload = {
        "model": "lm-studio/qwen3.5-9b",
        "messages": [
            {"role": "system", "content": "Ты профессиональный копирайтер, пишешь короткие продающие письма."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        resp = requests.post(
            f"{OMNIROUTE_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except:
        pass
    return ""


# Для тестирования
if __name__ == "__main__":
    print("=== OmniRoute Connection Test ===")
    print(f"URL: {OMNIROUTE_URL}")
    print(f"Connected: {check_omniroute_connection()}")
    
    # Тест анализа
    test_text = """
    ООО "Салон Красоты Этуаль"
    Адрес: г. Симферополь, ул. Горького, 15
    Телефон: +7 978 123-45-67
    Email: info@etual-crimea.ru
    
    Директор салона: Петрова Анна Сергеевна
    Учредитель: Петров Сергей Иванович
    
    Мы работаем для вас с 9:00 до 21:00
    Запись по телефону или через форму на сайте
    """
    
    import asyncio
    async def test():
        result = await analyze_page_with_ai(test_text, "Салон Красоты Этуаль")
        print("\n=== AI Analysis Result ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
