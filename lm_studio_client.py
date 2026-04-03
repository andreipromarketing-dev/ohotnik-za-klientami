"""
AI Integration для LM-Studio — прямой вызов без OmniRoute
"""
import os
import json
import aiohttp

LM_STUDIO_URL = "http://127.0.0.1:1234/v1"

DEFAULT_MODEL = "aya-expanse-8b"

EXTRACT_CONTACTS_PROMPT = """Найди контактные данные компании.

JSON:
{"emails": [], "people": [{"name": "Имя", "position": "должность", "type": "owner|director"}]}

Только реальные данные. Не выдумывай."""


async def call_lm_studio(system_prompt: str, user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Прямой запрос к LM-Studio API (OpenAI-совместимый)"""
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
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
    
    user_message = f"Компания: {company_name}\n\nТекст страницы:\n{page_text[:5000]}"
    
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
    except:
        return False


def get_available_models() -> list:
    """Получает список доступных моделей"""
    try:
        import requests
        resp = requests.get(f"http://127.0.0.1:1234/v1/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [m.get("id") for m in data.get("data", [])]
    except:
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
