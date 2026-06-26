"""
AI Integration для LM-Studio — прямой вызов без OmniRoute
"""
import os
import json
import aiohttp

LM_STUDIO_URL = "http://127.0.0.1:1234/v1"

DEFAULT_MODEL = "aya-expanse-8b"

EXTRACT_CONTACTS_PROMPT = """Извлеки ВСЕ контактные данные компании из текста страницы.

Формат JSON:
{
  "emails": ["admin@company.ru", "info@company.ru"],
  "phones": ["+7 978 123-45-67", "8 800 100-00-00"],
  "vk": "vk.com/username или vk.com/id123456",
  "telegram": "username (без @)",
  "people": [
    {"name": "Имя Фамилия", "position": "должность", "type": "owner|director|founder|manager"}
  ]
}

ПРАВИЛА:
- Извлекай ТОЛЬКО реальные данные, которые ЯВНО присутствуют в тексте
- НЕ выдумывай и НЕ дополняй недостающие данные
- Email: ищи в тексте, в Schema.org разметке, в href=mailto:
- Телефоны: любой формат (+7, 8, цифры с тире/пробелами/скобками)
- VK: vk.com/username, m.vk.com/username, @username
- Telegram: t.me/username, @username (брось @ при записи)
- Люди: директор, гендиректор, учредитель, владелец, founder, CEO, управляющий
- Если данных нет — возвращай пустые массивы {}

Примеры:
- "info@salon.ru" → emails: ["info@salon.ru"]
- "тел: 8 978 123-45-67" → phones: ["89781234567"]
- "vk.com/durov" → vk: "vk.com/durov"
- "Наш TG: @mycompany" → telegram: "mycompany"
- "Директор: Иванова М.И." → people: [{"name": "Иванова", "position": "директор", "type": "director"}]"""


async def call_lm_studio(system_prompt: str, user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Прямой запрос к LM-Studio API (OpenAI-совместимый)"""
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1000,
        "temperature": 0
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LM_STUDIO_URL}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    try:
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


async def analyze_page_with_ai(page_text: str, company_name: str = "", model: str = DEFAULT_MODEL) -> dict:
    """Анализирует текст страницы и извлекает контактную информацию"""
    
    user_message = f"Компания: {company_name}\n\nТекст страницы:\n{page_text[:10000]}"
    
    result = await call_lm_studio(EXTRACT_CONTACTS_PROMPT, user_message, model)
    
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


def check_lm_studio() -> bool:
    """Проверяет доступность LM-Studio"""
    try:
        import requests
        resp = requests.get(f"http://127.0.0.1:1234/v1/models", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def get_available_models() -> list:
    """Получает список доступных моделей"""
    try:
        import requests
        resp = requests.get(f"http://127.0.0.1:1234/v1/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [m.get("id") for m in data.get("data", [])]
    except Exception:
        pass
    return []


if __name__ == "__main__":
    print("=== LM-Studio Connection Test ===")
    print(f"URL: {LM_STUDIO_URL}")
    print(f"Available: {check_lm_studio()}")
    print(f"Models: {get_available_models()}")
    
    test_text = """
    ООО "Салон Красоты"
    Тел: +7 978 123-45-67
    Email: info@salon.ru
    
    Директор: Иванова Мария
    Учредитель: Петров Сергей
    """
    
    import asyncio
    async def test():
        result = await analyze_page_with_ai(test_text, "Салон Красоты")
        print("\n=== Result ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
