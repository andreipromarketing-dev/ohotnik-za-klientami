# UI Улучшения API - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task.

**Goal:** Улучшить интерфейс управления API в боковой панели - добавить переключатели, цветовую маркировку, исправить кнопки.

**Architecture:** Доработать существующий код в sidebar секции app.py - добавить переключатели (checkboxes) для выбора API, цветовую маркировку типов, унифицировать кнопки.

**Tech Stack:** Streamlit, Python, Base64 encoding для хранения.

---

### Task 1: Добавить переключатели (рубильники) для выбора API

**Files:**
- Modify: `app.py:135-220` (секция sidebar API управления)

- [ ] **Step 1: Прочитать текущий код**

Прочитать строки 135-230 в app.py для понимания текущей структуры.

- [ ] **Step 2: Добавить переключатели после списка API**

```python
# Секция переключателей
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Выбор API")

# Выбор поискового API
search_options = ["🔍 Поиск", *st.session_state.custom_apis.keys() if st.session_state.custom_apis else []]
selected_search = st.sidebar.radio("Для поиска:", search_options, horizontal=True)

# Выбор LLM API  
llm_options = ["🤖 LLM", *st.session_state.custom_apis.keys() if st.session_state.custom_apis else []]
selected_llm = st.sidebar.radio("Для обогащения:", llm_options, horizontal=True)
```

- [ ] **Step 3: Сохранить выбор в session_state**

```python
if "selected_search_api" not in st.session_state:
    st.session_state.selected_search_api = None
if "selected_llm_api" not in st.session_state:
    st.session_state.selected_llm_api = None
```

- [ ] **Step 4: Тестировать**

---

### Task 2: Цветовая маркировка API по типам

**Files:**
- Modify: `app.py:150-160` (секция показа кастомных API)

- [ ] **Step 1: Прочитать текущий код**

Строки 150-160 - показ кастомных API.

- [ ] **Step 2: Добавить цветовую маркировку**

```python
# Показ кастомных API с цветовой маркировкой
if st.session_state.custom_apis:
    st.sidebar.markdown("##### 📦 Кастомные API")
    for name, api_data in st.session_state.custom_apis.items():
        icon = "🔍" if api_data['type'] == 'search' else "🤖"
        # Цвет для поиска - синий, для LLM - фиолетовый
        color = "#3b82f6" if api_data['type'] == 'search' else "#8b5cf6"
        st.sidebar.markdown(f":[{color}]{icon} **{name}** ({api_data['type']})")
```

- [ ] **Step 3: Тестировать**

---

### Task 3: Исправить кнопки Сохранить/Отмена

**Files:**
- Modify: `app.py:190-210` (секция модального окна)

- [ ] **Step 1: Прочитать текущий код**

Строки 189-210.

- [ ] **Step 2: Изменить на одинаковые колонки с разными цветами**

```python
col_save, col_cancel = st.sidebar.columns(2)

if col_save.button("💾 Сохранить", use_container_width=True, type="primary"):
    if api_name and api_key:
        st.session_state.custom_apis[api_name] = {
            "type": "search" if api_type == "🔍 Поиск" else "llm",
            "key": api_key,
            "url": api_url,
            "model": api_model if api_type == "🤖 LLM" else None
        }
        save_custom_apis(st.session_state.custom_apis)
        st.session_state.show_api_modal = False
        st.sidebar.success("✅ API сохранён!")
        time.sleep(1)
        st.rerun()
    else:
        st.sidebar.error("Введите название и ключ!")

if col_cancel.button("✖ Отмена", use_container_width=True):
    st.session_state.show_api_modal = False
    st.rerun()
```

- [ ] **Step 3: Тестировать**

---

### Task 4: Добавить подписи "Для поиска" и "Для обогащения"

**Files:**
- Modify: `app.py` (секция переключателей из Task 1)

- [ ] **Step 1: Добавить понятные подписи**

```python
# Подписи с пояснениями
st.sidebar.caption("🔍 - для поиска компаний (SEO)")
st.sidebar.caption("🤖 - для обогащения данных AI")
```

- [ ] **Step 2: Тестировать**

---

### Task 5: Проверить работоспособность приложения

**Files:**
- Проверка: `app.py`, `search_providers.py`

- [ ] **Step 1: Проверить синтаксис**

```bash
python -c "import app; print('OK')"
```

- [ ] **Step 2: Проверить импорты**

```bash
python -c "import search_providers; print('OK')"
```

- [ ] **Step 3: Запустить приложение локально**

```bash
streamlit run app.py
```

- [ ] **Step 4: Проверить основные функции**

1. Открыть в браузере http://localhost:8501
2. Проверить загрузку UI
3. Проверить кнопку "Добавить API"
4. Проверить переключатели

---

## Проверка покрытия

- [x] Переключатели (рубильники) для выбора API
- [x] Цветовая маркировка по типам
- [x] Кнопки одинакового размера, разного цвета
- [x] Подписи "Для поиска" / "Для обогащения"
- [x] Проверка работоспособности