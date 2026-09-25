import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

WORKFLOWS_DIR = Path.home() / ".ohotnik" / "workflows"

AI_CONTEXT_SYSTEM_PROMPT = """Ты — эксперт по B2B-парсингу и настройке поисковых воркфлоу для парсера "Охотник за B2B-клиентами"."

Парсер работает в два этапа:
1. Поиск: DuckDuckGo (или SearchApi) собирает сырые данные по ключевым словам + маркерам
2. Обогащение: AI-модель парсит найденные сайты, извлекает контакты (телефон, email, соцсети) и определяет ЛПР

Твоя задача — адаптировать search-параметры воркфлоу под конкретную B2B-задачу пользователя."""

AI_CONTEXT_TASK = """Адаптируй search.keywords и search.primary_markers / search.secondary_markers под следующую задачу пользователя:

{prompt}

Если пользователь не указал конкретные города или лимит — сохрани их как есть."""

AI_CONTEXT_RULES = """Правила:
1. Keywords — B2B-ниши, не бренды. Каждое слово — отдельный поисковый запрос.
2. primary_markers — основные типы страниц для поиска контактов (официальный сайт, контакты, телефон, ООО).
3. secondary_markers — дополнительные (о компании, email, ИП, лицензия).
4. Исключи тату/пирсинг из результатов.
5. Не добавляй unrelated keywords.
6. markers должны быть направлены на поиск контактных данных организации.
7. Сохрани структуру JSON, меняй только keywords, primary_markers, secondary_markers если не указано иное."""

AI_CONTEXT_OUTPUT = """Верни ТОЛЬКО валидный JSON, без пояснений. Сохрани всю структуру, меняй только keywords, primary_markers, secondary_markers."""


class Workflow:
    def __init__(self, data=None):
        if data:
            self.data = data
        else:
            self.data = self._default()

    def _default(self):
        return {
            "workflow": {
                "name": "Новый воркфлоу",
                "description": "",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
            },
            "search": {
                "keywords": [],
                "primary_markers": ["официальный сайт", "контакты", "телефон", "ООО"],
                "secondary_markers": ["о компании", "email", "ИП"],
                "cities": [],
                "limit": 500,
                "exclude_keywords": ["тату", "пирсинг"],
            },
            "enrichment": {
                "ai_provider": "Groq",
                "ai_model": "openai/gpt-oss-120b",
            },
        }

    def to_json(self, include_ai_context=True, user_prompt=""):
        data = dict(self.data)
        if include_ai_context:
            prompt_text = user_prompt if user_prompt else "[опишите вашу задачу]"
            data["ai_context"] = {
                "system_prompt": AI_CONTEXT_SYSTEM_PROMPT,
                "task": AI_CONTEXT_TASK.format(prompt=prompt_text),
                "rules": AI_CONTEXT_RULES,
                "output_format": AI_CONTEXT_OUTPUT,
            }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str):
        try:
            data = json.loads(json_str)
            if "workflow" not in data or "search" not in data:
                raise ValueError("Неверный формат: отсутствуют поля workflow/search")
            return cls(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Неверный JSON: {e}")

    def save(self, name=None):
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        name = (name or self.data["workflow"]["name"]).strip()
        if not name:
            name = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.data["workflow"]["updated"] = datetime.now().isoformat()
        path = WORKFLOWS_DIR / f"{name}.json"
        path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, name):
        path = WORKFLOWS_DIR / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Workflow не найден: {name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data)

    @staticmethod
    def list_library():
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        workflows = []
        for f in sorted(WORKFLOWS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                wf = data.get("workflow", {})
                workflows.append({
                    "name": f.stem,
                    "description": wf.get("description", ""),
                    "modified": wf.get("updated", ""),
                })
            except Exception:
                pass
        return workflows

    @staticmethod
    def delete(name):
        path = WORKFLOWS_DIR / f"{name}.json"
        if path.exists():
            path.unlink()

    @staticmethod
    def build_from_current(niche_name, niche_data, cities, limit, ai_provider, ai_model):
        keywords = niche_data.get("keywords", [niche_name])
        return Workflow({
            "workflow": {
                "name": f"{niche_name}_{datetime.now().strftime('%Y%m%d')}",
                "description": f"Поиск: {niche_name}",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
            },
            "search": {
                "keywords": keywords,
                "primary_markers": ["официальный сайт", "контакты", "телефон", "ООО"],
                "secondary_markers": ["о компании", "email", "ИП"],
                "cities": cities if isinstance(cities, list) else [cities],
                "limit": limit or 500,
                "exclude_keywords": [],
            },
            "enrichment": {
                "ai_provider": ai_provider,
                "ai_model": ai_model,
            },
        })
