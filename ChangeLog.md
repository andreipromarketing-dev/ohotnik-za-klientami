# Changelog

## v3.6 (2026-07-05)

### Added
- **Workflow system** — JSON export/import of search configuration (niche, cities, keywords, markers, limit, exclude list)
- **AI context in export** — exported JSON includes `ai_context` block (system prompt, task, rules, output format) for LLM fine-tuning
- **Workflow library** — save/load/delete presets in `~/.ohotnik/workflows/`
- **Multi-city search** — multiselect from 48 cities + "Вся Россия" checkbox
- **Exclude keywords filter** — words to filter out from results by name/URL/address (default: тату, пирсинг)
- **Limit slider** — 20–1000 configurable company limit (default 500)
- **Workflow override** — when a workflow is active, its keywords/markers/cities/limit/exclude prefill and override manual inputs
- **Delete feedback** — success message shown after deleting a workflow from library

### Fixed
- **NameError in Export/Save** — workflow expander moved after category/cities/params widgets so all UI variables exist before Export/Save buttons reference them
- **Dead `seen_urls` set** — removed write-only dedup variable that was never read
- **Code review fixes** — 10 issues resolved across `search_providers.py`, `app.py`, `workflow.py` (dead code, missing parameters, path sanitization, JSON validation, hardcoded paths, error logging)

### Changed
- README updated with workflow documentation and updated file structure
- `config.py` — added `WORKFLOWS_DIR` constant

## v3.5 (2026-07-04)

- Multi-key failover for Groq API
- Live table updates during enrichment
- Timeout fix for slow AI responses

## v3.4 (2026-07-03)

- Auto-save/resume checkpoints every 20 sites
- Emil Kowalski UI polish (animations, micro-interactions)
- Fixed resume duplication bug
- Fixed `set+set` crash

## v3.3 (2026-06-28)

- Fixed white screen on startup
- Groq API status check
- Aggregator threshold tuning
- Punycode domain support
- Progress bar fixes
