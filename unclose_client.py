"""
AI Integration для UncloseAI - бесплатный OpenAI-совместимый API без ключей
"""
import json
import aiohttp

# Эндпоинты с сайта (без ключей)
HERMES_URL = "https://hermes.ai.unturf.com/v1"
QWEN_URL = "https://qwen.ai.unturf.com/v1"

DEFAULT_MODEL = "hermes-3-llama-3.1-405b"

MODELS = {
    "hermes-3-llama-3.1-405b": "Hermes 3 Llama 3.1 405B",
    "hermes-3-llama-3.1-70b": "Hermes 3 Llama 3.1 70B",
    "Qwen/Qwen2.5-72B-Instruct": "Qwen 2.5 72B (код)",
    "Qwen/Qwen2.5-32B-Instruct": "Qwen 2.5 32B",
    "Qwen/Qwen2.5-Coder-32B-Instruct": "Qwen Coder 32B",
}

EXTRACT_CONTACTS_PROMPT = """Найди контактные данные компании.

JSON:
{"emails": [], "people": [{"name": "Имя", "position": "должность", "type": "owner|director"}]}

Только реальные данные. Не выдумывай."""


async def call_unclose(system_prompt: str, user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Запрос к UncloseAI API (OpenAI-совместимый, без ключей)"""
    
    # Выбираем эндпоинт в зависимости от модели
    if model.startswith("Qwen"):
        base_url = QWEN_URL
    else:
        base_url = HERMES_URL
    
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
                f"{base_url}/chat/completions",
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
    """Анализирует текст страницы и извлекает контактную информацию через UncloseAI"""
    
    user_message = f"Компания: {company_name}\n\nТекст страницы:\n{page_text[:5000]}"
    
    result = await call_unclose(EXTRACT_CONTACTS_PROMPT, user_message, model)
    
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


def check_unclose() -> bool:
    """Проверяет доступность UncloseAI API"""
    try:
        import requests
        resp = requests.get(f"{HERMES_URL}/models", timeout=10)
        return resp.status_code == 200
    except:
        return False


def get_available_models() -> dict:
    """Возвращает список доступных моделей"""
    return MODELS


if __name__ == "__main__":
    print("=== UncloseAI Connection Test ===")
    print(f"Available: {check_unclose()}")
    print(f"Models: {list(MODELS.keys())}")