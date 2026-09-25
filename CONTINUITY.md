# CONTINUITY.md — Session Ledger

**Mandatory. Read at the start of every assistant turn. Update after each turn with goal/constraints/decisions/state changes.**

## Ledger Snapshot

- Goal (incl. success criteria): полный рефакторинг обогащения контактов — повысить полноту извлечения email/VK/TG с ~40% до >85% recall. Успех = метрика: доля лидов с Email/VK/TG после прогона на test corpus.
- Constraints/Assumptions: Streamlit app, enricher.py — основной код, 3 AI-провайдера (LM Studio/Groq/Unclose), Playwright для парсинга. НЕ менять CSS темы без подтверждения.
- Key decisions:
  - Режим: Build Mode (разрешены правки)
  - Приоритет: полный рефакторинг (Bug-1 → H1-H6 → M1-M6 → L1-L3 → tests → verify)
  - Зависимости: beautifulsoup4, extruct, email-validator (проверить в requirements)
  - Тесты: unit + integration (автоматические, Андрей не участвует в ручном запуске)
- State: Phase 0 in_progress — подготовка
- Done: аудит кода (3 агента), best practices research, план внедрения, выбор полного рефакторинга
- Now: Phase 0 — CONTINUITY.md + зависимости
- Next: Phase 1 — Bug-1 + Bug-2-4
- Open questions:
  - requirements.txt — есть ли там beautifulsoup4, extruct, email-validator?
  - Запуск тестов — через pytest?
- Working set (files/ids/commands): enricher.py, groq_client.py, lm_studio_client.py, unclose_client.py, search_providers.py, config.py, requirements.txt

## Session Log

### Turn 1 (2026-05-13)
- Андрей: пропускает много email/VK/TG — запрос на улучшение
- Агенты: explore(enricher audit), general(best practices), explore(test corpus plan)
- Результат аудита: критический баг ai_emails не мержатся, JSON-LD не парсится, href не читается, wait_until недостаточный
- Андрей выбрал: полный рефакторинг
- План: 6 фаз (0→6), 25+ тестов

### Turn 3 (2026-09-25)
- Андрей: "Грок не подключен" в запущенном приложении — запрос диагностики
- Диагноз (проверено живыми запросами):
  - Баг А: check_groq() использует requests+certifi → SSL CERTIFICATE_VERIFY_FAILED
    (self-signed cert в цепочке: антивирус/провайдерский MITM, CA есть только в Windows store).
    curl (Windows store) → TLS OK; aiohttp → 200. Ключ ВАЛИДЕН.
  - Баг Б: DEFAULT_MODEL llama-3.1-8b-instant → 404 model_not_found (декомиссирована).
    Из MODELS живы только openai/gpt-oss-120b и openai/gpt-oss-20b (сверено с /v1/models).
  - Следствие: сайдбар "Groq: Не настроен" + enricher.py:697 гейтит AI-обогащение через
    check_ai_groq() → Groq-обогащение молча никогда не запускается.
  - Приложение работает: порт 8501 OPEN.
- State: жду решения Андрея по варианту фикса

### Turn 4 (2026-09-25) — фикс Groq по варианту 1 (DONE)
- В groq_client.py:
  - DEFAULT_MODEL: llama-3.1-8b-instant → openai/gpt-oss-20b (404→200, проверено)
  - MODELS: оставлены только 3 живые (gpt-oss-20b/120b, qwen3.8-27b — все 200)
  - check_groq(): requests+certifi → urllib + системное хранилище Windows
    (причина: self-signed CA в цепочке) + кастомный User-Agent
    (причина 2: Cloudflare 1010 банит UA Python-urllib)
  - Добавлен check_groq_detail() → стадии no_keys/ok/invalid_key/api_error/network
  - .env подхватывается и при прямом запуске (load_dotenv в модуле)
- В app.py: сайдбар показывает 4 состояния вместо бинарного
- Верификация: check_groq()=True (оба ключа из GROQ_API_KEY валидны, failover цел),
  py_compile чистый, pytest 30/30 passed
- DeepSeek-ключ от Андрея: 401 Authentication Fails — НЕВАЛИДЕН,
  в .env НЕ добавлял. Жду верный ключ → тогда сделаю deepseek_client.py + провайдер
- ВАЖНО: нужен перезапуск Streamlit (код изменён + кэш статуса 300 сек)

### Turn 5 (2026-09-25) — путаница «где Groq в списке» (DONE)
- Андрей после перезапуска: в выпадающем списке нет "Groq", но 3 модели есть;
  сайдбар показывает Groq активен; вопрос — какая модель обогащает
- Причина: не баг. Groq выбирается в radio «Провайдер AI» (кружки слева),
  а выпадающий список показывает МОДЕЛИ выбранного провайдера.
  Сайдбар-индикатор ≠ выбор: он лишь говорит «ключ рабочий».
- Фикс: добавлена строка-подсказка под AI-настройками
  «Обогащение будет делать: {провайдер} / {модель}» (app.py, без CSS-правок)
- py_compile OK. Нужна перезагрузка страницы в браузере (rerun подхватит сам)

### Turn 6 (2026-09-25) — живой статус-бар и таблица (DONE, build mode)
- Симптом Андрея: в автопоиске нет динамических обновлений таблицы и статус-бара
- Причины: таблица рисовалась раз в 20 лидов; лог копился в памяти до конца прогона;
  обновления обёрнуты в молчаливый except; плюс после фикса Groq AI-шаг реально
  заработал → каждый сайт стал обрабатываться дольше (раньше AI молча пропускался)
- Правки в app.py (CSS не трогал):
  - _ui_error(): ошибки отрисовки идут в лог + терминал, больше не молчим
  - _render_live_log(): последние 5 строк лога живым блоком при баре
  - _run_enrichment_flow и resume-блок «Продолжить»: таблица каждые 5 лидов,
    живой лог на каждом лиде, финальная отрисовка остатка (<5), ошибки наружу
- Верификация: py_compile чистый, pytest 30/30,
  headless AppTest: exceptions=[], подсказка и «Groq: Подключен» на месте
- Нужно: перезапустить Streamlit (изменён app.py)

## Implementation Complete (2026-05-13)

### Done:
- **Bug-1**: ai_emails теперь мержатся в res['emails'] (enricher.py)
- **Bug-2**: VK regex расширен (m.vk.com, vk.cc)
- **Bug-3**: TG regex расширен (+ для invite links, @username mentions)
- **H1**: добавлен _extract_from_html() — mailto/VK/TG из href атрибутов
- **H2**: добавлен _extract_from_jsonld() — Schema.org контакты
- **H3**: добавлен _extract_from_meta() — Open Graph email
- **M2**: HTML unescape перед regex
- **AI prompts**: расширены (emails+phones+vk+telegram+people, max_tokens=1000, text[:10000])
- **Confidence scoring**: добавлен LLM fallback для edge cases с <2 контактами
- **VK/TG from AI**: ai_vk/ai_telegram теперь мержатся в результат
- **tests/**: 30 unit tests, 30 passed

### Dependencies added:
beautifulsoup4, extruct, email-validator, w3lib

### Files modified:
enricher.py, groq_client.py, lm_studio_client.py, unclose_client.py, requirements.txt, CONTINUITY.md, tests/test_enricher.py, tests/__init__.py, tests/conftest.py

## Текущие баги (к исправлению)

### Критический баг
- **Bug-1** (enricher.py:163-173): `ai_emails` вычисляются в AI-клиентах, но НИКОГДА не мержатся в `res['emails']`. AI находит email, но они теряются.

### Пропускаемые паттерны
- **Bug-2**: VK `m.vk.com`, `vk.cc` — subdomain не предусмотрен в regex
- **Bug-3**: TG `t.me/+` (invite links), `+` не в классе символов
- **Bug-4**: `@username` TG из plain text — ищется только `t.me/`

### Неиспользуемые источники
- **H1**: `href="mailto:..."` — не читается
- **H2**: JSON-LD / Schema.org — не парсится
- **H3**: Open Graph meta — не парсится

## План фаз

| Фаза | Содержание | Priority |
|------|-----------|----------|
| 0 | CONTINUITY.md + зависимости | HIGH |
| 1 | Bug-1 + Bug-2-4 | HIGH |
| 2 | H1 + H2 + H3 | HIGH |
| 3 | M1 + M2 + M3-M6 (AI prompts) | MEDIUM |
| 4 | Confidence scoring + LLM fallback | MEDIUM |
| 5 | tests/ unit + integration | MEDIUM |
| 6 | Верификация | MEDIUM |