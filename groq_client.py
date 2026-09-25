"""
AI Integration для Groq - быстрый облачный API
Автоматический failover между несколькими API ключами
"""
import os
import json
import aiohttp
import asyncio

# Подхватываем .env и без config.py (чтобы работал и прямой запуск файла)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except Exception:
    pass

GROQ_URL = "https://api.groq.com/openai/v1"
# Проверен живьём 25.09.2026 (HTTP 200 на /chat/completions)
DEFAULT_MODEL = "openai/gpt-oss-20b"

# Только модели, подтверждённые живым запросом 25.09.2026.
# Остальные (llama-3.1-8b-instant, mixtral, gemma2, deepseek-r1, qwen3.6)
# декомиссированы Groq → 404 model_not_found.
MODELS = {
    "openai/gpt-oss-20b": "GPT OSS 20B (быстрый, по умолчанию)",
    "openai/gpt-oss-120b": "GPT OSS 120B (умный)",
    "qwen/qwen3.8-27b": "Qwen 3.8 27B",
}

# --- Multi-key support ---

def _collect_keys() -> list:
    """Собирает все API ключи из переменных окружения"""
    keys = []
    # Основной ключ (может быть несколько через запятую)
    main = os.getenv("GROQ_API_KEY", "").strip()
    if main:
        for k in main.split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
    # Дополнительные ключи GROQ_API_KEY_1, GROQ_API_KEY_2, ... до 10
    for i in range(1, 11):
        k = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys

GROQ_API_KEYS = _collect_keys()

def _log(msg: str):
    try:
        print(f"[Groq] {msg}")
    except Exception:
        pass

# --- Failover state ---

class _KeyManager:
    def __init__(self, keys: list):
        self.keys = keys
        self._idx = 0
        self._blacklist = set()  # ключи, которые вернули 403

    def current(self) -> str:
        if not self.keys:
            return ""
        return self.keys[self._idx]

    def rotate(self):
        """Переключается на следующий неплохой ключ"""
        tried = set()
        while len(tried) < len(self.keys):
            self._idx = (self._idx + 1) % len(self.keys)
            k = self.keys[self._idx]
            if k not in self._blacklist:
                return k
            tried.add(k)
        return ""

    def mark_bad(self, key: str):
        """Помечает ключ как плохой (403)"""
        self._blacklist.add(key)
        _log(f"Ключ ...{key[-8:]} помечен как недоступный")
        self.rotate()

    def has_keys(self) -> bool:
        return len([k for k in self.keys if k not in self._blacklist]) > 0

    def reset(self):
        self._blacklist.clear()
        self._idx = 0

_key_mgr = _KeyManager(GROQ_API_KEYS)

# --- Prompts ---

EXTRACT_CONTACTS_PROMPT = """Извлеки ВСЕ контактные данные компании из текста страницы.

Формат JSON:
{
  "emails": ["admin@company.ru", "info@company.ru"],
  "phones": ["+7 978 123-45-67", "8 800 100-00-00"],
  "vk": "vk.com/username или vk.com/id123456",
  "telegram": "username (без @)",
  "address": "г. Новосибирск, ул. Ленина, д. 1, оф. 101",
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
- Address: полный юридический или фактический адрес компании
- Люди: директор, гендиректор, учредитель, владелец, founder, CEO, управляющий
- Если данных нет — возвращай пустые массивы {}

Примеры:
- "info@salon.ru" → emails: ["info@salon.ru"]
- "тел: 8 978 123-45-67" → phones: ["89781234567"]
- "vk.com/durov" → vk: "vk.com/durov"
- "Наш TG: @mycompany" → telegram: "mycompany"
- "Адрес: г. Краснодар, ул. Красная, д. 100" → address: "г. Краснодар, ул. Красная, д. 100"
- "Директор: Иванова М.И." → people: [{"name": "Иванова", "position": "директор", "type": "director"}]"""


async def call_groq(system_prompt: str, user_message: str, model: str = DEFAULT_MODEL) -> dict:
    """Запрос к Groq API с авто-failover между ключами"""

    if not _key_mgr.has_keys():
        return {"error": "Нет доступных GROQ ключей"}

    last_error = ""
    for attempt in range(len(GROQ_API_KEYS)):
        key = _key_mgr.current()
        if not key:
            _key_mgr.rotate()
            continue

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 1000,
            "temperature": 0
        }

        headers = {
            "Authorization": f"Bearer {key}",
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
                            _log(f"OK (ключ ...{key[-8:]})")
                            return json.loads(content.strip())
                        except json.JSONDecodeError:
                            return {"error": "JSON parse failed", "raw": content[:500]}

                    error_text = await resp.text()
                    last_error = f"API error {resp.status}: {error_text[:200]}"
                    _log(f"{resp.status} для ключа ...{key[-8:]}: {last_error}")

                    # 403/401 = ключ невалиден → ротируем
                    if resp.status in (401, 403):
                        _key_mgr.mark_bad(key)
                        continue
                    # Другие ошибки (429, 500) — тоже ротируем
                    _key_mgr.rotate()

        except asyncio.TimeoutError:
            last_error = "Timeout"
            _log(f"Timeout для ключа ...{key[-8:]}")
            _key_mgr.rotate()
        except Exception as e:
            last_error = str(e)
            _log(f"Ошибка для ключа ...{key[-8:]}: {e}")
            _key_mgr.rotate()

    return {"error": f"Все ключи недоступны. Последняя ошибка: {last_error}"}


async def analyze_page_with_ai(page_text: str, company_name: str = "", model: str = DEFAULT_MODEL) -> dict:
    """Анализирует текст страницы и извлекает контактную информацию через Groq"""

    user_message = f"Компания: {company_name}\n\nТекст страницы:\n{page_text[:6500]}"

    result = await call_groq(EXTRACT_CONTACTS_PROMPT, user_message, model)

    if "error" not in result:
        phones_raw = result.get("phones", [])
        vk_raw = result.get("vk", "")
        tg_raw = result.get("telegram", "")
        return {
            "ai_emails": result.get("emails", []),
            "ai_phones": phones_raw if isinstance(phones_raw, list) else [phones_raw] if phones_raw else [],
            "ai_address": result.get("address", ""),
            "ai_vk": vk_raw if isinstance(vk_raw, str) else "",
            "ai_telegram": tg_raw if isinstance(tg_raw, str) else "",
            "ai_socials": result.get("socials", {}),
            "ai_people": result.get("people", []),
            "ai_contacts": result.get("contacts", {}),
            "ai_confidence": result.get("confidence", 0),
            "ai_success": True
        }
    else:
        return {
            "ai_emails": [],
            "ai_phones": [],
            "ai_address": "",
            "ai_vk": "",
            "ai_telegram": "",
            "ai_socials": {},
            "ai_people": [],
            "ai_contacts": {},
            "ai_confidence": 0,
            "ai_success": False,
            "ai_error": result.get("error")
        }


def check_groq_detail() -> dict:
    """Детальная проверка подключения.

    Возвращает {"ok": bool, "stage": str, "hint": str}, где stage:
      no_keys     — нет GROQ_API_KEY в окружении/.env
      ok          — ключ принят, API отвечает
      invalid_key — ключ отклонён (401/403)
      api_error   — API отвечает, но с другой ошибкой
      network     — сеть/сертификат/таймаут (до API не достучались)

    Использует urllib + системное хранилище сертификатов Windows, а НЕ
    requests+certifi: certifi не знает локальный CA (антивирус/провайдер)
    и падает с SSL CERTIFICATE_VERIFY_FAILED даже при валидном ключе.
    Синхронная — безопасно вызывается из async-кода обогатителя.
    """
    import ssl
    import urllib.request
    import urllib.error

    if not _key_mgr.has_keys():
        return {"ok": False, "stage": "no_keys", "hint": "Нет GROQ_API_KEY в .env"}
    key = _key_mgr.current()
    if not key:
        return {"ok": False, "stage": "no_keys", "hint": "Все ключи помечены недоступными"}

    payload = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    }).encode()
    req = urllib.request.Request(
        f"{GROQ_URL}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # Без этого Cloudflare перед Groq режет запрос кодом 1010
            # ("banned browser"): дефолтный UA Python-urllib в бан-листе
            "User-Agent": "OhotnikZaKlientami/1.0 (Windows)",
        },
        method="POST",
    )
    try:
        # create_default_context() на Windows подхватывает системное
        # хранилище (CryptoAPI) — локальный CA там есть, handshake проходит
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            if resp.status == 200:
                return {"ok": True, "stage": "ok", "hint": f"HTTP 200, модель {DEFAULT_MODEL}"}
            return {"ok": False, "stage": "api_error", "hint": f"HTTP {resp.status}"}
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            _key_mgr.mark_bad(key)
            return {"ok": False, "stage": "invalid_key",
                    "hint": f"Ключ ...{key[-8:]} отклонён (HTTP {e.code})"}
        return {"ok": False, "stage": "api_error", "hint": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "stage": "network",
                "hint": f"{type(e).__name__}: {str(e)[:120]}"}


def check_groq() -> bool:
    """Совместимая обёртка: True/False (используется гейтом в enricher.py)"""
    return check_groq_detail()["ok"]


def get_available_models() -> dict:
    """Возвращает список доступных моделей"""
    return MODELS


if __name__ == "__main__":
    print("=== Groq Connection Test ===")
    print(f"Keys found: {len(GROQ_API_KEYS)}")
    for i, k in enumerate(GROQ_API_KEYS):
        print(f"  Key {i+1}: ...{k[-8:]}")
    print(f"Has available keys: {_key_mgr.has_keys()}")
    print(f"Available: {check_groq()}")
    print(f"Models: {list(MODELS.keys())}")