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

### Turn 2 (2026-05-13)
- Андрей: "Приступай. Тесты решаются программно - производи."
- Режим: Build Mode
- State: Phase 5 (test) completed

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