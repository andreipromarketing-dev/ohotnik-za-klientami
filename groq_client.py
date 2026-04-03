"""
AI Integration для Groq - быстрый облачный API
"""
import os
import json
import aiohttp

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1"

DEFAULT_MODEL = "llama-3.1-8b-instant"

MODELS = {
    "llama-3.1-8b-instant": "Llama 3.1 8B (быстрый)",
    "llama-3.1-70b-versatile": "Llama 3.1 70B (мощный)",
    "llama-3.3-70b-versatile": "Llama 3.3 70B (новый)",
    "mixtral-8x7b-32768": "Mixtral 8x7B",
    "gemma2-9b-it": "Gemma 2 9B",
    "deepseek-r1-distill-llama-70b": "DeepSeek R1 (reasoning)",
}

EXTRACT_CONTACTS_PROMPT = """Найди контактные данные компании.

JSON:
{"emails": [], "people": [{"name": "Имя", "position": "должность", "type": "owner|director"}]}

Только реальные данные. Не выдумывай."""


async def call_groq(system_prompt: str, user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Запрос к Groq API (OpenAI-совместимый)"""
    
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY не настроен"}
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GROQ_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
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
    """Анализирует текст страницы и извлекает контактную информацию через Groq"""
    
    user_message = f"Компания: {company_name}\n\nТекст страницы:\n{page_text[:5000]}"
    
    result = await call_groq(EXTRACT_CONTACTS_PROMPT, user_message, model)
    
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


def check_groq() -> bool:
    """Проверяет доступность Groq API"""
    if not GROQ_API_KEY:
        return False
    try:
        import requests
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        resp = requests.get(f"{GROQ_URL}/models", timeout=5)
        return resp.status_code == 200
    except:
        return False


def get_available_models() -> dict:
    """Возвращает список доступных моделей"""
    return MODELS


if __name__ == "__main__":
    print("=== Groq Connection Test ===")
    print(f"API Key: {'Настроен' if GROQ_API_KEY else 'НЕ НАСТРОЕН'}")
    print(f"Available: {check_groq()}")
    print(f"Models: {list(MODELS.keys())}")