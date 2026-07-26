import streamlit as st
import pandas as pd
import time
from datetime import datetime
import config
import io
import sys
import asyncio
import enricher
import search_providers
import json
import base64
import os
import subprocess
from pathlib import Path
import workflow as wf
import base64

API_STORE_FILE = Path(__file__).parent / ".api_keys.enc"
LOGO_PATH = Path(r"F:\СОЦИТУД\AI-Эксперт\ЮгСпецСети\Фотошопное\Иконки\logo_small.svg")

def load_custom_apis():
    """Загружает кастомные API из файла"""
    if API_STORE_FILE.exists():
        try:
            decoded = base64.b64decode(API_STORE_FILE.read_text().encode())
            return json.loads(decoded.decode())
        except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError):
            return {}
    return {}

def save_custom_apis(apis):
    """Сохраняет кастомные API в файл (Base64 кодирование)"""
    encoded = base64.b64encode(json.dumps(apis).encode()).decode()
    with open(API_STORE_FILE, 'w') as f:
        f.write(encoded)

def play_sound():
    """Воспроизводит звуковое уведомление"""
    try:
        import winsound
        winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_NOWAIT)
    except Exception:
        pass

st.set_page_config(page_title="ЮгСпецСети | Охотник за клиентами", page_icon="🎯", layout="wide")

# ============================================================================
# CSS — ТЁМНАЯ ТЕМА (#012F46)
# ============================================================================

st.markdown("""
<style>
/* ====================================================================
   ТЁМНАЯ ТЕМА #012F46 — Emil Kowalski design engineering standards
   ==================================================================== */

/* --- CSS Variables --- */
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --dur-fast: 150ms;
  --dur-normal: 200ms;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.25);
}

/* --- Base --- */
.stApp { background: #012F46 !important; }
.main { background: #012F46 !important; }

/* --- Sidebar --- */
section[data-testid="stSidebar"] { background: #013a5c !important; }
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] .stMarkdown { color: #b0c4d4 !important; }

/* --- Buttons: tactile feedback --- */
.stButton > button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"] {
    color: #0D1117 !important;
    background: #E8F9EE !important;
    border: none !important;
    transition: transform var(--dur-fast) var(--ease-out),
                background var(--dur-normal) ease,
                box-shadow var(--dur-fast) ease !important;
}
.stButton > button p,
.stButton > button span { color: #0D1117 !important; }
.stButton > button:hover {
    background: #d4f4e3 !important;
    box-shadow: 0 2px 8px rgba(232,249,238,0.25) !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
}
.stButton > button:focus-visible {
    outline: 2px solid #E8F9EE !important;
    outline-offset: 2px !important;
}
.stDownloadButton > button {
    color: #0D1117 !important;
    background: #E8F9EE !important;
    transition: transform var(--dur-fast) var(--ease-out),
                background var(--dur-normal) ease !important;
}
.stDownloadButton > button:active { transform: scale(0.97) !important; }

/* --- Inputs: smooth focus ring --- */
input,
.stTextInput > div > div > input,
textarea,
.stTextArea > div > div > textarea {
    background: #024d82 !important;
    color: #ffffff !important;
    border: 1px solid #024d82 !important;
    transition: border-color var(--dur-fast) ease,
                box-shadow var(--dur-fast) ease !important;
}
input::placeholder, textarea::placeholder { color: #b0c4d4 !important; }
input:focus, textarea:focus {
    border-color: #E8F9EE !important;
    box-shadow: 0 0 0 1px #E8F9EE !important;
}
input:focus-visible, textarea:focus-visible {
    outline: 2px solid #E8F9EE !important;
    outline-offset: 2px !important;
}

/* --- Select / Multiselect --- */
.stSelectbox > div > div,
.stMultiSelect > div > div,
[data-baseweb="select"] {
    background: #024d82 !important;
    color: #ffffff !important;
    border: 1px solid #024d82 !important;
    transition: border-color var(--dur-fast) ease,
                box-shadow var(--dur-fast) ease !important;
}
.stSelectbox, .stSelectbox *,
.stMultiSelect, .stMultiSelect * {
    color: #ffffff !important;
}
[data-baseweb="select"]:focus-within {
    border-color: #E8F9EE !important;
    box-shadow: 0 0 0 1px #E8F9EE !important;
}
.stMultiSelect span[data-baseweb="tag"] {
    background: #013a5c !important;
    color: #E8F9EE !important;
}
.stMultiSelect span[data-baseweb="tag"] * {
    color: #E8F9EE !important;
    fill: #E8F9EE !important;
}
.stMultiSelect input::placeholder,
.stSelectbox input::placeholder {
    color: #b0c4d4 !important;
}

/* --- Radio: smooth toggle --- */
.stRadio > div, [role="radiogroup"] { color: #ffffff !important; }
.stRadio div[role="radiogroup"] label {
    color: #b0c4d4 !important;
    transition: background var(--dur-fast) ease,
                color var(--dur-fast) ease !important;
}
.stRadio div[role="radiogroup"] label:has(input:checked) {
    background: #E8F9EE !important;
    color: #0D1117 !important;
    border-radius: 4px;
}

/* --- Checkbox --- */
.stCheckbox > label, [role="checkbox"] { color: #ffffff !important; }

/* --- Expander: depth + smooth hover --- */
.streamlit-expander, details {
    background: #013a5c !important;
    border: 1px solid #024d82 !important;
    border-radius: 6px;
    box-shadow: var(--shadow-sm) !important;
}
.streamlit-expander summary, details summary {
    color: #ffffff !important;
    transition: background var(--dur-fast) ease !important;
}
.streamlit-expander summary:hover, details summary:hover {
    background: #024d82 !important;
}

/* --- Slider --- */
.stSlider [role="slider"] { background: #E8F9EE !important; }
.stSlider .stMarkdown { color: #b0c4d4 !important; }

/* --- Progress: smooth fill --- */
.stProgress > div > div { background: #E8F9EE !important; }
.stProgress > div > div > div {
    background: #E8F9EE !important;
    transition: width 300ms var(--ease-out) !important;
}

/* --- Spinner --- */
.stSpinner > div {
    border: 3px solid #013a5c !important;
    border-top: 3px solid #E8F9EE !important;
}

/* --- Metrics --- */
[data-testid="stMetricValue"] { color: #E8F9EE !important; }
[data-testid="stMetricLabel"] { color: #b0c4d4 !important; }

/* --- DataFrame: depth + row stagger animation --- */
.stDataFrame, [data-testid="stDataFrame"] {
    background: #013a5c !important;
    box-shadow: var(--shadow-sm) !important;
}
.stDataFrame thead th, [data-testid="stDataFrame"] thead th {
    background: #024d82 !important;
    color: #ffffff !important;
}

/* --- Header --- */
[data-testid="stHeader"], header { background: #012F46 !important; }
[data-testid="stToolbar"], header button, [role="menubutton"],
[data-testid="stToolbar"] button { color: #ffffff !important; }
[data-testid="stToolbar"] button:hover { background: #024d82 !important; }

/* --- Popover / Dropdown: ширина по содержимому --- */
[data-baseweb="popover"] {
    background: #012F46 !important;
    border: 1px solid #024d82 !important;
    box-shadow: var(--shadow-md) !important;
    width: auto !important;
    min-width: 300px !important;
    max-width: 520px !important;
    box-sizing: border-box !important;
}
[data-baseweb="popover"] * {
    color: #ffffff !important;
}
[data-baseweb="popover"] input {
    background: #024d82 !important;
    color: #ffffff !important;
}
[data-baseweb="popover"] input::placeholder {
    color: #b0c4d4 !important;
}

/* --- Context menu — фиксированная ширина --- */
[data-baseweb="menu"],
[role="menu"], div[role="menu"] {
    background: #012F46 !important;
    border: 1px solid #024d82 !important;
    box-shadow: var(--shadow-md) !important;
    width: 180px !important;
    min-width: 180px !important;
    max-width: 180px !important;
    box-sizing: border-box !important;
}
[data-baseweb="menu"] *, [role="menu"] *, [role="menuitem"] {
    color: #ffffff !important;
    background: #012F46 !important;
    width: 100% !important;
    max-width: 180px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    display: block !important;
    box-sizing: border-box !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] button:hover,
[role="menuitem"]:hover,
[role="menu"] li:hover {
    background: #024d82 !important;
}

/* --- Separator --- */
hr { border-color: #024d82 !important; }

/* --- Alerts: depth --- */
.stSuccess { background: #013a5c !important; color: #E8F9EE !important; box-shadow: var(--shadow-sm) !important; }
.stError { background: #5c1a01 !important; color: #ff9999 !important; box-shadow: var(--shadow-sm) !important; }
.stWarning { background: #5c4a01 !important; color: #ffeb99 !important; box-shadow: var(--shadow-sm) !important; }
.stInfo { background: #013a5c !important; color: #99ccff !important; box-shadow: var(--shadow-sm) !important; }

/* ====================================================================
   ANIMATIONS — Emil Kowalski philosophy
   ==================================================================== */

/* --- Title entrance --- */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.stApp h1, .stApp h2 {
    animation: fadeInUp 400ms var(--ease-out) both;
}

/* --- Row stagger for results table --- */
@keyframes fadeInRow {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* --- Reduced motion: accessibility --- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)

st.title("Охотник за B2B-клиентами")
st.markdown("**Агентство:** <strong style='color: #012F46 !important; font-weight: 800 !important; font-size: 1.1rem;'>ЮгСпецСети</strong> | Нейропродавец | Нейроассистент | AI для бизнеса", unsafe_allow_html=True)

# Инициализация состояний
if "logs" not in st.session_state:
    st.session_state.logs = []
if "hunter_data" not in st.session_state:
    st.session_state.hunter_data = [] 
if "raw_items" not in st.session_state:
    st.session_state.raw_items = []
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False
if "custom_apis" not in st.session_state:
    st.session_state.custom_apis = load_custom_apis()
if "checkpoint_info" not in st.session_state:
    # Проверяем наличие чекпоинта при старте
    cp = enricher.load_checkpoint()
    st.session_state.checkpoint_info = cp
if "workflow" not in st.session_state:
    st.session_state.workflow = None
if "workflow_name" not in st.session_state:
    st.session_state.workflow_name = None
if "show_import" not in st.session_state:
    st.session_state.show_import = False
if "confirm_delete_lib" not in st.session_state:
    st.session_state.confirm_delete_lib = None

def log_message(msg):
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.logs.append(f"[{timestamp}] {msg}")
        if len(st.session_state.logs) > 100:
            st.session_state.logs.pop(0)
    except Exception:
        pass

def _render_live_table(placeholder, export_ph, data):
    """Рисует таблицу + метрики + кнопку экспорта в плейсхолдер"""
    try:
        tmp_df = pd.DataFrame(data)
        with placeholder.container():
            st.dataframe(tmp_df, hide_index=True, width='stretch')
            cols = st.columns(4)
            cols[0].metric("Лидов", len(tmp_df))
            cols[1].metric("С телефонами", sum(1 for r in data if r.get("Телефон", "—") != "—"))
            cols[2].metric("С email", sum(1 for r in data if r.get("Email", "—") != "—"))
            cols[3].metric("Найден ЛПР", sum(1 for r in data if r.get("ЛПР", "—") != "—"))
        with export_ph.container():
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                tmp_df.to_excel(writer, index=False, sheet_name='Leads')
            st.download_button(
                "📥 Скачать Excel",
                data=buffer.getvalue(),
                file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                type="primary",
                key=f"live_export_{len(data)}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception:
        pass


def _run_enrichment_flow():
    """Запускает Шаг 2 (парсинг + AI) — вызывается из кнопки или авто-триггера"""
    st.session_state.stop_requested = False
    total = len(st.session_state.raw_items)
    log_message(f"🎯 Парсинг {total} компаний...")
    log_message(f"🤖 AI: {st.session_state.ai_provider} ({st.session_state.ai_model})")

    progress_bar = st.progress(0)
    stats_placeholder = st.empty()
    table_placeholder = st.empty()
    export_placeholder = st.empty()
    st.session_state.enrichment_active = True

    if sys.platform == 'win32':
        try: asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception: pass

    processed_data = []
    search_params = {
        "ai_provider": st.session_state.ai_provider,
        "ai_model": st.session_state.ai_model,
        "total": total,
        "raw_items": st.session_state.raw_items,
    }

    async def run_enrichment():
        count = 0
        try:
            async for result in enricher.batch_process(
                st.session_state.raw_items,
                log_func=log_message,
                use_ai=True,
                ai_provider=st.session_state.ai_provider,
                ai_model=st.session_state.ai_model,
                search_params=search_params
            ):
                if st.session_state.stop_requested:
                    log_message("🛑 Остановлено пользователем. Результаты сохранены.")
                    break

                count += 1
                processed_data.append(result)
                try:
                    progress_bar.progress(count / total)
                    stats_placeholder.info(f"📊 {count}/{total}")
                    if count % 20 == 0 and processed_data:
                        _render_live_table(table_placeholder, export_placeholder, processed_data)
                except Exception:
                    pass
        except Exception as e:
            log_message(f"⚠️ Прервано: {str(e)[:50]}. Сохраняем прогресс...")

        st.session_state.hunter_data = processed_data
        log_message("=" * 40)
        log_message(f"✅ ГОТОВО: {count} лидов")
        st.session_state.enrichment_active = False

    asyncio.run(run_enrichment())
    play_sound()
    st.success("✅ Парсинг + AI завершён!")


@st.cache_resource
@st.cache_data
def _cached_logo_b64():
    if LOGO_PATH.exists():
        try:
            svg = LOGO_PATH.read_text(encoding='utf-8')
            return "data:image/svg+xml;base64," + base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        except Exception:
            return None
    return None

# Логотип в боковой панели (в самом верху)
col_logo1, col_logo2, col_logo3 = st.sidebar.columns([1, 2, 1])
logo_b64 = _cached_logo_b64()
if logo_b64:
    col_logo2.markdown(
        f'<img src="{logo_b64}" style="width:200px;max-width:100%" alt="ЮгСпецСети">',
        unsafe_allow_html=True
    )
else:
    col_logo2.caption("ЮгСпецСети")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Режим работы")
auto_mode = st.sidebar.toggle(
    "🤖 Автоматический режим",
    value=st.session_state.get('auto_mode', False),
    help="Шаг 2 (парсинг+AI) запускается сразу после Шага 1 (поиска)"
)
st.session_state.auto_mode = auto_mode
if auto_mode:
    st.sidebar.success("🔄 Шаг 1 → Шаг 2 непрерывно")
else:
    st.sidebar.info("👆 Ручной запуск после проверки")

st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Статус API")
api_status = {
    "SearchApi.io": config.SEARCHAPI_API_KEY,
    "VK API": config.VK_TOKEN,
    "DuckDuckGo": "✅ Автоматически (безлимит)"
}
for name, key in api_status.items():
    if key and key != "✅ Автоматически (безлимит)":
        st.sidebar.success(f"✅ {name}: Активен")
    elif key == "✅ Автоматически (безлимит)":
        st.sidebar.success(f"✅ {name}")
    else:
        st.sidebar.warning(f"❌ {name}: Не настроен")

# Показ кастомных API с цветовой маркировкой
if st.session_state.custom_apis:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📦 Кастомные API")
    
    # Секция для поиска (синяя)
    search_apis = [(n, d) for n, d in st.session_state.custom_apis.items() if d['type'] == 'search']
    if search_apis:
        st.sidebar.markdown("🔍 **Поиск:**")
        for name, api_data in search_apis:
            st.sidebar.success(f"  ✅ {name}")
    
    # Секция для LLM (фиолетовая)
    llm_apis = [(n, d) for n, d in st.session_state.custom_apis.items() if d['type'] == 'llm']
    if llm_apis:
        st.sidebar.markdown("🤖 **Обогащение:**")
        for name, api_data in llm_apis:
            st.sidebar.success(f"  ✅ {name}")

# Показать сохранённые API
if st.session_state.custom_apis:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Сохранённые API")
    
    # Чекпоинты для Поиска (синий)
    search_apis = {k: v for k, v in st.session_state.custom_apis.items() if v['type'] == 'search'}
    if search_apis:
        st.sidebar.markdown("**🔍 Поиск:**")
        for name in search_apis:
            st.sidebar.caption(f"  ✅ {name}")
    
    # Чекпоинты для LLM (фиолетовый)
    llm_apis = {k: v for k, v in st.session_state.custom_apis.items() if v['type'] == 'llm'}
    if llm_apis:
        st.sidebar.markdown("**🤖 AI:**")
        for name in llm_apis:
            st.sidebar.caption(f"  ✅ {name}")
    
    st.sidebar.caption("⚠️ Кастомные API пока не интегрированы в pipeline")

try:
    from lm_studio_client import check_lm_studio, get_available_models as get_lm_models
    from groq_client import check_groq, get_available_models as get_groq_models
    from unclose_client import check_unclose, get_available_models as get_unclose_models
    
    @st.cache_resource(ttl=300)
    def _cached_check_groq():
        return check_groq()
    @st.cache_resource(ttl=300)
    def _cached_groq_models():
        return get_groq_models()
    
    if _cached_check_groq():
        st.sidebar.success("✅ Groq: Подключен")
    else:
        st.sidebar.warning("⚠️ Groq: Не настроен")
except Exception:
    st.sidebar.warning("⚠️ AI: Не настроен")

# Кнопка управления API
st.sidebar.markdown("---")
if st.sidebar.button("➕ Добавить API", width='stretch'):
    st.session_state.show_api_modal = True

# Модальное окно для добавления API
if st.session_state.get("show_api_modal", False):
    st.sidebar.markdown("### ➕ Добавить API")
    
    api_type = st.sidebar.radio("Тип:", ["🔍 Поиск", "🤖 LLM"], horizontal=True)
    api_name = st.sidebar.text_input("Название:", placeholder="Мой SearchAPI")
    
    if api_type == "🔍 Поиск":
        api_key = st.sidebar.text_input("API Key:", type="password", placeholder="Введите ключ")
        api_url = st.sidebar.text_input("URL (опционально):", placeholder="https://api.example.com")
    else:
        api_key = st.sidebar.text_input("API Key:", type="password", placeholder="sk-...")
        api_url = st.sidebar.text_input("Base URL:", placeholder="https://api.openai.com/v1")
        api_model = st.sidebar.text_input("Модель:", placeholder="gpt-4")
    
    col_save, col_cancel = st.sidebar.columns(2)

    # Кнопка зеленая 
    if col_save.button("✅ Сохранить", key="save_btn", width='stretch'):
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
            st.rerun()
        else:
            st.sidebar.error("Введите название и ключ!")

    # Кнопка красная 
    if col_cancel.button("❌ Отмена", key="cancel_btn", width='stretch'):
        st.session_state.show_api_modal = False
        st.rerun()

# Управление существующими API
if st.session_state.custom_apis:
    with st.sidebar.expander("⚙️ Управление API"):
        for name, api_data in st.session_state.custom_apis.items():
            c1, c2 = st.sidebar.columns([3, 1])
            c1.caption(f"**{name}** ({api_data['type']})")
            if c2.button("🗑️", key=f"del_{name}"):
                del st.session_state.custom_apis[name]
                save_custom_apis(st.session_state.custom_apis)
                st.rerun()

# Выбор AI провайдера и модели
st.header("AI Настройки")
ai_col1, ai_col2 = st.columns(2)

with ai_col1:
    ai_provider = st.radio(
        "Провайдер AI:",
        ["Groq", "UncloseAI", "LM Studio"],
        horizontal=True,
        help="Groq/UncloseAI - облачные (бесплатные), LM Studio - локальный"
    )

with ai_col2:
    ai_model = ""
    if ai_provider == "Groq":
        groq_models = _cached_groq_models()
        if groq_models:
            model_options = [(k, v) for k, v in groq_models.items()]
            model_labels = [f"{v} ({k})" for k, v in groq_models.items()]
            selected_idx = st.selectbox(
                "Модель:",
                range(len(model_labels)),
                format_func=lambda i: model_labels[i]
            )
            ai_model = model_options[selected_idx][0]
            st.caption("Лимит: 30 req/min, 40k токенов/мин")
        else:
            st.selectbox("Модель:", ["Модели не найдены"], disabled=True)
    elif ai_provider == "LM Studio":
        with st.spinner("Подключение к LM Studio..."):
            lm_models = get_lm_models()
        if lm_models:
            ai_model = st.selectbox("Модель:", lm_models, help="Выберите модель из LM Studio")
        else:
            st.selectbox("Модель:", ["LM Studio не запущен"], disabled=True)
            st.caption("Запустите LM Studio на localhost:1234")
    else:  # UncloseAI
        with st.spinner("Проверка UncloseAI..."):
            unclose_models = get_unclose_models()
        if unclose_models:
            model_options = [(k, v) for k, v in unclose_models.items()]
            model_labels = [f"{v} ({k})" for k, v in unclose_models.items()]
            selected_idx = st.selectbox(
                "Модель:",
                range(len(model_labels)),
                format_func=lambda i: model_labels[i]
            )
            ai_model = model_options[selected_idx][0]
            st.caption("Безлимит, не требует API ключа")
        else:
            st.selectbox("Модель:", ["UncloseAI недоступен"], disabled=True)
            st.caption("Сервис временно недоступен")

st.session_state.ai_provider = ai_provider
st.session_state.ai_model = ai_model

st.header("1. Настройка поиска")

is_wf_active = bool(st.session_state.workflow)
if is_wf_active:
    wf_name = st.session_state.workflow["workflow"]["name"]
    st.info(f"📄 Активен воркфлоу: **{wf_name}** — все параметры берутся из JSON. Поля отключены.")

# ============================================================================
# КАТЕГОРИЯ
# ============================================================================
niche_val_from_wf = st.session_state.workflow.get("search", {}) if is_wf_active else {}

c1, c2 = st.columns(2)
with c1:
    manual_niche = st.text_input("Категория бизнеса:", placeholder="Введите или выберите ниже",
                                 value="", key="niche_inp", disabled=is_wf_active)
    niche_options = ["Выбрать из списка...", *config.HUNTER_QUERIES.keys()]
    niche_idx = st.selectbox("Или выберите:", niche_options, key="niche_sel", label_visibility="collapsed", disabled=is_wf_active)
    niche = "" if niche_idx == "Выбрать из списка..." else niche_idx

# ============================================================================
# ГОРОДА — при активном workflow берутся из JSON
# ============================================================================
wf_cities = niche_val_from_wf.get("cities", []) if is_wf_active else []
all_city_names = list(config.REGION_COORDS.keys())

wf_whole_russia = wf_cities == ["вся россия"]
default_cities = [] if wf_whole_russia else [c for c in wf_cities if c in all_city_names]

if is_wf_active:
    st.text(f"🏙️ Города: {'Вся Россия' if wf_whole_russia else ', '.join(default_cities) if default_cities else '—'}")
else:
    selected_cities = st.multiselect(
        "Города:", all_city_names,
        default=default_cities,
        placeholder="Выберите города...",
        key="city_multiselect"
    )

    whole_russia = st.checkbox(
        "Вся Россия (поиск без города)",
        value=False,
        key="whole_russia"
    )

# ============================================================================
# ПАРАМЕТРЫ — лимит всегда adjustable, exclude — из workflow если активен
# ============================================================================
limit_val = st.slider("Кол-во компаний:", 20, 1000, 500, key="limit_slider")

if is_wf_active:
    wf_exclude = niche_val_from_wf.get("exclude_keywords", [])
    exclude_keywords = list(wf_exclude)
    if exclude_keywords:
        st.text(f"🚫 Исключено: {', '.join(exclude_keywords)}")
else:
    exclude_input = st.text_input(
        "Исключить слова (через запятую):",
        value="",
        key="exclude_input"
    )
    exclude_keywords = [x.strip() for x in exclude_input.split(",") if x.strip()]

# ============================================================================
# WORKFLOW — импорт/экспорт/библиотека
# ============================================================================
with st.expander("📦 Workflow (импорт/экспорт/библиотека)", expanded=False):
    col_w1, col_w2, col_w3 = st.columns([1, 1, 1])

    # Export
    if col_w1.button("📤 Export JSON", use_container_width=True):
        if st.session_state.workflow:
            export_wf = wf.Workflow(st.session_state.workflow)
        else:
            current_niche = manual_niche.strip() if manual_niche.strip() else niche
            niche_data = config.HUNTER_QUERIES.get(current_niche, {})
            export_wf = wf.Workflow.build_from_current(
                current_niche, niche_data, selected_cities,
                limit_val,
                st.session_state.get('ai_provider', 'Groq'),
                st.session_state.get('ai_model', '')
            )
        json_str = export_wf.to_json(include_ai_context=True, user_prompt="")
        st.code(json_str, language="json")
        st.download_button(
            "💾 Скачать JSON", data=json_str,
            file_name=f"{export_wf.data['workflow']['name']}.json",
            mime="application/json", key="dl_export"
        )

    # Import
    if col_w2.button("📥 Import JSON", use_container_width=True):
        st.session_state.show_import = True

    if col_w3.button("✕ Сбросить", use_container_width=True):
        st.session_state.workflow = None
        st.session_state.workflow_name = None
        st.session_state.show_import = False
        st.rerun()

    if st.session_state.show_import:
        import_tabs = st.tabs(["📁 Загрузить файл", "📋 Вставить текст"])
        with import_tabs[0]:
            uploaded = st.file_uploader("Выберите JSON файл", type=["json"], key="wf_file")
            if uploaded and st.button("📂 Загрузить файл", key="apply_import_file", use_container_width=True):
                try:
                    uploaded.seek(0)
                    content = uploaded.read().decode("utf-8")
                    wf_obj = wf.Workflow.from_json(content)
                    st.session_state.workflow = wf_obj.data
                    st.success(f"✅ Загружен: {wf_obj.data['workflow']['name']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
        with import_tabs[1]:
            text_json = st.text_area("Вставьте JSON воркфлоу:", height=200, key="wf_text")
            if st.button("Применить", key="apply_import_text"):
                if text_json.strip():
                    try:
                        wf_obj = wf.Workflow.from_json(text_json)
                        st.session_state.workflow = wf_obj.data
                        st.success(f"✅ Загружен: {wf_obj.data['workflow']['name']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")

    # Library save
    col_s1, col_s2 = st.columns([3, 1])
    lib_name = col_s1.text_input("Имя для сохранения:", placeholder="msk_bild_1", key="lib_save_name")
    if col_s2.button("💾 Сохранить", use_container_width=True):
        if lib_name.strip():
            if st.session_state.workflow:
                save_wf = wf.Workflow(st.session_state.workflow)
            else:
                current_niche = (manual_niche.strip() if manual_niche.strip() else niche) or "custom"
                niche_data = config.HUNTER_QUERIES.get(current_niche, {})
                save_wf = wf.Workflow.build_from_current(
                    current_niche, niche_data, selected_cities,
                    limit_val,
                    st.session_state.get('ai_provider', 'Groq'),
                    st.session_state.get('ai_model', '')
                )
            save_wf.save(lib_name.strip())
            st.success(f"✅ Сохранён: {lib_name}")
            st.rerun()

    # Library load
    library = wf.Workflow.list_library()
    if library:
        lib_options = {w["name"]: w for w in library}
        lib_keys = list(lib_options.keys())
        selected_lib = st.selectbox("📚 Загрузить из библиотеки", [""] + lib_keys, key="lib_select")
        if selected_lib:
            col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
            if col_l1.button("📂 Загрузить", use_container_width=True):
                try:
                    wf_obj = wf.Workflow.load(selected_lib)
                    st.session_state.workflow = wf_obj.data
                    st.session_state.workflow_name = selected_lib
                    st.success(f"✅ Загружен: {selected_lib}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
            if col_l2.button("🗑️ Удалить", use_container_width=True):
                st.session_state.confirm_delete_lib = selected_lib
                st.rerun()

            # Confirm delete dialog
            if st.session_state.confirm_delete_lib == selected_lib:
                st.warning(f"🗑️ Удалить воркфлоу **«{selected_lib}»**?")
                cc1, cc2 = st.columns(2)
                if cc1.button("Да, удалить", use_container_width=True):
                    wf.Workflow.delete(selected_lib)
                    st.session_state.confirm_delete_lib = None
                    st.rerun()
                if cc2.button("Отмена", use_container_width=True):
                    st.session_state.confirm_delete_lib = None
                    st.rerun()

            if col_l3.button("📂 Открыть папку", use_container_width=True):
                folder = Path(config.WORKFLOWS_DIR).expanduser().resolve()
                folder.mkdir(parents=True, exist_ok=True)
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", str(folder)])
                else:
                    subprocess.Popen(["xdg-open", str(folder)])

st.header("2. Управление")
if not config.SEARCHAPI_API_KEY:
    st.error("⚠️ **Внимание:** Не настроен SearchApi.io. Добавьте ключ в файл `.env`.")

col_start, col_ai, col_stop = st.columns([1.5, 1.5, 1])

has_step1 = bool(st.session_state.get('raw_items'))

step1_type = "secondary" if has_step1 else "primary"
step2_type = "primary" if has_step1 else "secondary"

if col_start.button("🚀 ШАГ 1. Поиск", type=step1_type, width='stretch'):
    st.session_state.stop_requested = False
    st.session_state.raw_items = []
    st.session_state.hunter_data = []

    # Определяем keywords, markers, города, лимит — из workflow или UI
    if st.session_state.workflow:
        sw = st.session_state.workflow["search"]
        final_keywords = sw.get("keywords", [])
        primary_markers = sw.get("primary_markers", config.PRIMARY_MARKERS)
        secondary_markers = sw.get("secondary_markers", config.SECONDARY_MARKERS)
        final_markers = primary_markers + secondary_markers
        limit_val = sw.get("limit", 500)
        exclude_keywords = sw.get("exclude_keywords", [])
        wf_cities = sw.get("cities", [])
        if wf_cities == ["вся россия"]:
            target_cities = ["вся россия"]
        else:
            target_cities = [c for c in wf_cities if c in list(config.REGION_COORDS.keys())]
        log_message(f"📄 Workflow: {st.session_state.workflow['workflow']['name']}")
        if not final_keywords:
            st.error("❌ В workflow нет ключевых слов (keywords)")
            st.stop()
        if not target_cities:
            st.error("❌ В workflow нет городов (cities)")
            st.stop()
    elif manual_niche.strip():
        current_niche = manual_niche.strip()
        final_keywords = [current_niche]
        primary_markers = config.PRIMARY_MARKERS
        secondary_markers = config.SECONDARY_MARKERS
        final_markers = primary_markers + secondary_markers
        if whole_russia:
            target_cities = ["вся россия"]
        elif selected_cities:
            target_cities = list(selected_cities)
        else:
            st.error("❌ Выберите хотя бы один город или включите 'Вся Россия'")
            st.stop()
    else:
        current_niche = niche
        if not current_niche:
            st.error("❌ Укажите категорию (введите или выберите из списка)")
            st.stop()
        niche_val = config.HUNTER_QUERIES.get(niche, {})
        if isinstance(niche_val, dict):
            final_keywords = niche_val.get("keywords", [])
        else:
            final_keywords = niche_val if isinstance(niche_val, list) else [niche_val]
        primary_markers = config.PRIMARY_MARKERS
        secondary_markers = config.SECONDARY_MARKERS
        final_markers = primary_markers + secondary_markers
        # Города для ручного режима
        if whole_russia:
            target_cities = ["вся россия"]
        elif selected_cities:
            target_cities = list(selected_cities)
        else:
            st.error("❌ Выберите хотя бы один город или включите 'Вся Россия'")
            st.stop()

    log_message(f"📝 Ключевых слов: {len(final_keywords)}, маркеров: {len(final_markers)}")
    log_message(f"🏙️ Городов: {len(target_cities)}")

    seen_names = set()
    results = []

    log_placeholder = st.empty()
    progress_bar = st.progress(0)

    def live_log(msg):
        log_message(msg)
        log_placeholder.info(msg)

    async def run_search():
        total_phase1 = len(target_cities) * len(final_keywords) * len(primary_markers)
        total_phase2 = len(target_cities) * len(final_keywords) * len(secondary_markers)
        total_queries = total_phase1 + total_phase2
        query_count = 0

        for city in target_cities:
            if st.session_state.stop_requested: break
            if city == "вся россия":
                city_label = "Вся Россия"
                live_log(f"🏙️ Поиск по всей России...")
            else:
                city_label = city
                live_log(f"🏙️ Город: {city}...")

            # Фаза 1: Primary
            for keyword in final_keywords:
                if st.session_state.stop_requested: break
                for marker in primary_markers:
                    if st.session_state.stop_requested: break
                    if city == "вся россия":
                        query = f"{keyword} {marker}".strip()
                    else:
                        query = f"{keyword} {city} {marker}".strip()
                    query_count += 1
                    live_log(f"📡 [{query_count}/{total_queries}] {query}")
                    progress_bar.progress(min(query_count / total_queries, 1.0))

                    batch = await search_providers.fetch_companies(
                        query, limit_val, log_func=live_log, exclude_keywords=exclude_keywords
                    )
                    for item in batch:
                        name = item.get('name', '').strip().lower()
                        url = (item.get('websites') or [''])[0]
                        if name and name not in seen_names:
                            seen_names.add(name)
                            item["city"] = city_label
                            results.append(item)

                    if len(results) >= limit_val:
                        break
                if len(results) >= limit_val:
                    break
            if len(results) >= limit_val:
                break

            # Фаза 2: Secondary (если мало)
            if len(results) < limit_val:
                live_log(f"🔄 Добавляем secondary маркеры ({len(results)}/{limit_val})...")
                for keyword in final_keywords:
                    if st.session_state.stop_requested: break
                    for marker in secondary_markers:
                        if st.session_state.stop_requested: break
                        if city == "вся россия":
                            query = f"{keyword} {marker}".strip()
                        else:
                            query = f"{keyword} {city} {marker}".strip()
                        query_count += 1
                        live_log(f"📡 [{query_count}/{total_queries}] {query}")
                        progress_bar.progress(min(query_count / total_queries, 1.0))

                        batch = await search_providers.fetch_companies(
                            query, limit_val, log_func=live_log, exclude_keywords=exclude_keywords
                        )
                        for item in batch:
                            name = item.get('name', '').strip().lower()
                            url = (item.get('websites') or [''])[0]
                            if name and name not in seen_names:
                                seen_names.add(name)
                                item["city"] = city_label
                                results.append(item)
                        if len(results) >= limit_val:
                            break
                    if len(results) >= limit_val:
                        break

                if len(results) >= limit_val:
                    break

        progress_bar.progress(1.0)

    with st.spinner("🔍 Идёт поиск компаний..."):
        asyncio.run(run_search())

    st.session_state.raw_items = results[:limit_val]
    st.session_state.hunter_data = [{
        "Компания": x.get('name', '—'),
        "Сайт": (x.get('websites') or [None])[0] or "—",
        "Телефон": (x.get('phones') or ['—'])[0],
        "VK": "—",
        "TG": "—",
        "MAX": "—",
        "Email": "—",
        "ЛПР": "—",
        "Адрес": x.get('addr', '—'),
        "Город": x.get('city', '—'),
    } for x in st.session_state.raw_items]

    if results:
        st.success(f"✅ Успешно собрано {len(st.session_state.raw_items)} компаний. Переходите к обогащению!")
        if st.session_state.get('auto_mode'):
            st.session_state.auto_enrich_pending = True
    else:
        st.error("❌ Ничего не найдено или проверьте API-ключи.")
    st.rerun()

# Авто-триггер: Шаг 2 запускается сразу после Шага 1
if st.session_state.get('auto_enrich_pending') and has_step1:
    if not st.session_state.get('enrichment_active'):
        st.session_state.auto_enrich_pending = False
        _run_enrichment_flow()

if col_ai.button("🔍 ШАГ 2. Парсинг + AI", type=step2_type, disabled=not st.session_state.raw_items, width='stretch'):
    _run_enrichment_flow()

# Кнопки "Продолжить" / "Удалить" предыдущую сессию
if st.session_state.get('checkpoint_info'):
    cp_results, cp_urls, cp_params, cp_raw, cp_names = st.session_state.checkpoint_info
    if cp_results:
        st.info(f"💾 Найден чекпоинт: {len(cp_results)} обработанных, {len(cp_urls)} URL")
        cc_cp1, cc_cp2 = st.columns(2)
        if cc_cp1.button("▶️ Продолжить предыдущую сессию", type="primary", use_container_width=True):
            st.session_state.stop_requested = False
            # База — результаты из чекпоинта (уже обогащённые)
            st.session_state.hunter_data = list(cp_results)
            
            # Восстанавливаем raw_items из чекпоинта если нет текущих
            if not st.session_state.raw_items and cp_raw:
                st.session_state.raw_items = cp_raw
            
            # Фильтруем по ИМЕНИ компании (не по URL — URL может измениться из-за редиректа)
            remaining = [item for item in st.session_state.raw_items 
                        if item.get('name', '').strip() not in cp_names]
            
            if not remaining:
                st.success("✅ Все компании уже обработаны в предыдущей сессии!")
            else:
                total = len(remaining)
                log_message(f"▶️ Продолжаем: {total} компаний осталось")
                log_message(f"🤖 AI: {st.session_state.ai_provider} ({st.session_state.ai_model})")
                
                progress_bar = st.progress(0)
                stats_placeholder = st.empty()
                table_placeholder = st.empty()
                export_placeholder = st.empty()
                st.session_state.enrichment_active = True
                
                if sys.platform == 'win32':
                    try: asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    except Exception: pass

                processed_data = []
                search_params = {
                    "ai_provider": st.session_state.ai_provider,
                    "ai_model": st.session_state.ai_model,
                    "total": total,
                    "raw_items": remaining,
                }
                
                async def run_resume():
                    count = 0
                    try:
                        async for result in enricher.batch_process(
                            remaining,
                            log_func=log_message,
                            use_ai=True,
                            ai_provider=st.session_state.ai_provider,
                            ai_model=st.session_state.ai_model,
                            processed_urls=cp_urls,
                            search_params=search_params
                        ):
                            if st.session_state.stop_requested:
                                log_message("🛑 Остановлено. Результаты сохранены.")
                                break
                            count += 1
                            processed_data.append(result)
                            try:
                                progress_bar.progress(count / total)
                                stats_placeholder.info(f"📊 {count}/{total}")
                                if count % 20 == 0 and processed_data:
                                    _render_live_table(table_placeholder, export_placeholder, processed_data)
                            except Exception:
                                pass
                    except Exception as e:
                        log_message(f"⚠️ Прервано: {str(e)[:50]}. Сохраняем прогресс...")
                    
                    st.session_state.hunter_data = list(cp_results) + processed_data
                    log_message("=" * 40)
                    log_message(f"✅ ГОТОВО: {count} новых лидов (всего {len(cp_results) + len(processed_data)})")
                    st.session_state.enrichment_active = False
                
                asyncio.run(run_resume())
                play_sound()
                st.success("✅ Продолжение завершено!")
            
            # Удаляем чекпоинт после успешного возобновления
            enricher.delete_checkpoint()
            st.session_state.checkpoint_info = None
            st.rerun()

    if cc_cp2.button("🗑️ Удалить и начать заново", use_container_width=True):
        enricher.delete_checkpoint()
        st.session_state.checkpoint_info = None
        st.rerun()

if col_stop.button("🛑 СТОП", width='stretch'):
    st.session_state.stop_requested = True
    st.rerun()

# Таблица и логи
st.header("3. Результаты")
if st.session_state.hunter_data:
    df = pd.DataFrame(st.session_state.hunter_data)
    st.dataframe(df, hide_index=True, width='stretch')
    
    # Статистика
    cols = st.columns(4)
    cols[0].metric("Лидов", len(df))
    cols[1].metric("С телефонами", sum(1 for r in st.session_state.hunter_data if r.get("Телефон", "—") != "—"))
    cols[2].metric("С email", sum(1 for r in st.session_state.hunter_data if r.get("Email", "—") != "—"))
    cols[3].metric("Найден ЛПР", sum(1 for r in st.session_state.hunter_data if r.get("ЛПР", "—") != "—"))
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    st.download_button(
        label="📥 Скачать Excel",
        data=buffer.getvalue(),
        file_name=f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        type="primary",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    if st.button("🗑️ Очистить"):
        st.session_state.hunter_data = []
        st.session_state.raw_items = []
        st.session_state.logs = []
        st.rerun()

with st.expander("📝 Технический лог", expanded=st.session_state.get('enrichment_active', False)):
    st.code("\n".join(st.session_state.logs[::-1]))

# Footer
st.markdown("---")
st.markdown("**ЮгСпецСети | Охотник v3.0** | югспецсети.рф | t.me/Concreator")
