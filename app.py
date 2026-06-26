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
from pathlib import Path
from PIL import Image

API_STORE_FILE = Path(__file__).parent / ".api_keys.enc"
LOGO_PATH = Path(r"F:\СОЦИТУД\AI-Эксперт\ЮгСпецСети\Фотошопное\Иконки\150.jpg")

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
/* ТЁМНАЯ ТЕМА (#012F46) — прямые селекторы */
.stApp {
    background: #012F46 !important;
}
.main {
    background: #012F46 !important;
}
section[data-testid="stSidebar"] {
    background: #013a5c !important;
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stMarkdown {
    color: #b0c4d4 !important;
}
.stButton > button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"] {
    color: #0D1117 !important;
    background: #E8F9EE !important;
    border: none !important;
}
.stButton > button p,
.stButton > button span {
    color: #0D1117 !important;
}
.stButton > button:hover {
    background: #d4f4e3 !important;
}
input,
.stTextInput > div > div > input,
textarea,
.stTextArea > div > div > textarea {
    background: #024d82 !important;
    color: #ffffff !important;
    border: 1px solid #024d82 !important;
}
input::placeholder,
textarea::placeholder {
    color: #b0c4d4 !important;
}
.stSelectbox > div > div,
[data-baseweb="select"] {
    background: #024d82 !important;
    color: #ffffff !important;
    border: 1px solid #024d82 !important;
}
[data-baseweb="select"] * {
    color: #ffffff !important;
}
.stRadio > div,
[role="radiogroup"] {
    color: #ffffff !important;
}
.stRadio div[role="radiogroup"] label:has(input:checked) {
    background: #E8F9EE !important;
    color: #0D1117 !important;
    border-radius: 4px;
}
.stRadio div[role="radiogroup"] label {
    color: #b0c4d4 !important;
}
.stCheckbox > label,
[role="checkbox"] {
    color: #ffffff !important;
}
.streamlit-expander,
details {
    background: #013a5c !important;
    border: 1px solid #024d82 !important;
    border-radius: 4px;
}
.streamlit-expander summary,
details summary {
    color: #ffffff !important;
}
.streamlit-expander summary:hover,
details summary:hover {
    background: #024d82 !important;
}
.stSlider [role="slider"] {
    background: #E8F9EE !important;
}
.stSlider .stMarkdown {
    color: #b0c4d4 !important;
}
.stProgress > div > div {
    background: #E8F9EE !important;
}
.stProgress > div > div > div {
    background: #E8F9EE !important;
}
.stSpinner > div {
    border: 3px solid #013a5c !important;
    border-top: 3px solid #E8F9EE !important;
}
[data-testid="stMetricValue"] {
    color: #E8F9EE !important;
}
[data-testid="stMetricLabel"] {
    color: #b0c4d4 !important;
}
.stDataFrame,
[data-testid="stDataFrame"] {
    background: #013a5c !important;
}
.stDataFrame thead th,
[data-testid="stDataFrame"] thead th {
    background: #024d82 !important;
    color: #ffffff !important;
}
.stDownloadButton > button {
    color: #0D1117 !important;
    background: #E8F9EE !important;
}
[data-testid="stHeader"],
header {
    background: #012F46 !important;
}
[data-testid="stToolbar"],
header button,
[role="menubutton"],
[data-testid="stToolbar"] button {
    color: #ffffff !important;
}
[data-testid="stToolbar"] button:hover {
    background: #024d82 !important;
}
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="menu"],
[role="menubar"],
div[role="menu"],
div[role="dialog"] {
    background: #012F46 !important;
    border: 1px solid #024d82 !important;
    width: 180px !important;
    min-width: 180px !important;
    max-width: 180px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}
[data-baseweb="menu"] *,
[role="menu"] *,
[role="menuitem"] {
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
    color: #ffffff !important;
}
hr {
    border-color: #024d82 !important;
}
.stSuccess {
    background: #013a5c !important;
    color: #E8F9EE !important;
}
.stError {
    background: #5c1a01 !important;
    color: #ff9999 !important;
}
.stWarning {
    background: #5c4a01 !important;
    color: #ffeb99 !important;
}
.stInfo {
    background: #013a5c !important;
    color: #99ccff !important;
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

def log_message(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")
    if len(st.session_state.logs) > 100:
        st.session_state.logs.pop(0)

@st.cache_resource
def _cached_logo():
    if LOGO_PATH.exists():
        try:
            return Image.open(LOGO_PATH)
        except (OSError, IOError):
            return None
    return None

# Логотип в боковой панели (в самом верху)
col_logo1, col_logo2, col_logo3 = st.sidebar.columns([1, 2, 1])
img = _cached_logo()
if img:
    col_logo2.image(img, width=120)
else:
    col_logo2.caption("ЮгСпецСети")

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
if st.sidebar.button("➕ Добавить API", use_container_width=True):
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
    if col_save.button("✅ Сохранить", key="save_btn", use_container_width=True):
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
    if col_cancel.button("❌ Отмена", key="cancel_btn", use_container_width=True):
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

# Блок выбора аудитории
st.header("1. Настройка поиска")

c1, c2, c3 = st.columns(3)
with c1:
    manual_niche = st.text_input("Категория бизнеса:", placeholder="Введите или выберите ниже", key="niche_inp")
    # Selectbox с опцией "Выбрать из списка..." как первой
    niche_options = ["Выбрать из списка...", *config.HUNTER_QUERIES.keys()]
    niche_idx = st.selectbox("Или выберите:", niche_options, key="niche_sel", label_visibility="collapsed")
    niche = "" if niche_idx == "Выбрать из списка..." else niche_idx
with c2:
    manual_city = st.text_input("Город:", placeholder="Введите или выберите ниже", key="city_inp")
    # Selectbox с опцией "Выбрать из списка..." как первой
    city_options = ["Выбрать из списка...", *config.REGION_COORDS.keys()]
    city_idx = st.selectbox("Или выберите:", city_options, key="city_sel", label_visibility="collapsed")
    region = "" if city_idx == "Выбрать из списка..." else city_idx
with c3:
    limit = st.slider("Кол-во компаний:", 10, 500, 50, 10)

st.header("2. Управление")
if not config.SEARCHAPI_API_KEY:
    st.error("⚠️ **Внимание:** Не настроен SearchApi.io. Добавьте ключ в файл `.env`.")

col_start, col_ai, col_stop = st.columns([1.5, 1.5, 1])

has_step1 = bool(st.session_state.get('raw_items'))

step1_type = "secondary" if has_step1 else "primary"
step2_type = "primary" if has_step1 else "secondary"

if col_start.button("🚀 ШАГ 1. Поиск", type=step1_type, use_container_width=True):
    st.session_state.stop_requested = False
    st.session_state.raw_items = []
    st.session_state.hunter_data = []
    
    # Определяем что используем: ручной ввод имеет приоритет над выбором из списка
    current_city = manual_city.strip() if manual_city.strip() else region
    current_niche = manual_niche.strip() if manual_niche.strip() else niche
    
    # Проверка что пользователь что-то выбрал или ввёл
    if not current_city:
        st.error("❌ Укажите город (введите или выберите из списка)")
        st.stop()
    if not current_niche:
        st.error("❌ Укажите категорию (введите или выберите из списка)")
        st.stop()
    
    log_message(f"🔍 DEBUG: current_city='{current_city}', current_niche='{current_niche}'")
    
    # Определяем ключевые слова и маркеры
    if manual_niche.strip():
        # Кастомная ниша — одно ключевое слово + стандартные маркеры
        final_keywords = [manual_niche.strip()]
        final_markers = config.PRIMARY_MARKERS + config.SECONDARY_MARKERS
    else:
        # Выбор из списка — новая структура с маркерами
        niche_val = config.HUNTER_QUERIES.get(niche, {})
        if isinstance(niche_val, dict):
            final_keywords = niche_val.get("keywords", [])
            final_markers = config.PRIMARY_MARKERS + config.SECONDARY_MARKERS
        else:
            # Фallback для старой структуры (если вдруг осталась)
            final_keywords = niche_val if isinstance(niche_val, list) else [niche_val]
            final_markers = config.PRIMARY_MARKERS + config.SECONDARY_MARKERS
    
    log_message(f"🎯 Категория: {current_niche}")
    log_message(f"📝 Ключевых слов: {len(final_keywords)}, маркеров: {len(final_markers)}")
    
    seen_names = set()
    seen_urls = set()
    results = []
    
    # Placeholder для live-лога
    log_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    def live_log(msg):
        log_message(msg)
        log_placeholder.info(msg)
    
    async def run_search():
        total_queries = len(final_keywords) * (len(config.PRIMARY_MARKERS) + len(config.SECONDARY_MARKERS))
        query_count = 0
        
        # Фаза 1: Primary маркеры (официальный сайт, контакты, реквизиты, телефон, ООО)
        primary_markers = config.PRIMARY_MARKERS
        for keyword in final_keywords:
            if st.session_state.stop_requested: break
            for marker in primary_markers:
                if st.session_state.stop_requested: break
                query = f"{keyword} {current_city} {marker}".strip()
                query_count += 1
                live_log(f"📡 [{query_count}/{total_queries}] {query}")
                progress_bar.progress(query_count / total_queries)
                
                batch = await search_providers.fetch_companies(query, limit, log_func=live_log)
                for item in batch:
                    name = item.get('name', '').strip().lower()
                    url = (item.get('websites') or [''])[0]
                    if name and name not in seen_names:
                        seen_names.add(name)
                        if url:
                            seen_urls.add(url)
                        results.append(item)
                
                if len(results) >= limit:
                    live_log(f"✅ Достигнут лимит: {len(results)} компаний")
                    break
            if len(results) >= limit:
                break
        
        # Фаза 2: Secondary маркеры (только если мало результатов)
        if len(results) < limit:
            secondary_markers = config.SECONDARY_MARKERS
            live_log(f"🔄 Мало результатов ({len(results)}), добавляем secondary маркеры...")
            for keyword in final_keywords:
                if st.session_state.stop_requested: break
                for marker in secondary_markers:
                    if st.session_state.stop_requested: break
                    query = f"{keyword} {current_city} {marker}".strip()
                    query_count += 1
                    live_log(f"📡 [{query_count}/{total_queries}] {query}")
                    progress_bar.progress(min(query_count / total_queries, 1.0))
                    
                    batch = await search_providers.fetch_companies(query, limit, log_func=live_log)
                    for item in batch:
                        name = item.get('name', '').strip().lower()
                        url = (item.get('websites') or [''])[0]
                        if name and name not in seen_names:
                            seen_names.add(name)
                            if url:
                                seen_urls.add(url)
                            results.append(item)
                    
                    if len(results) >= limit:
                        live_log(f"✅ Достигнут лимит: {len(results)} компаний")
                        break
                if len(results) >= limit:
                    break
        
        progress_bar.progress(1.0)
    
    with st.spinner("🔍 Идёт поиск компаний..."):
        asyncio.run(run_search())
    
    st.session_state.raw_items = results[:limit]
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
    } for x in st.session_state.raw_items]
    
    if results:
        st.success(f"✅ Успешно собрано {len(st.session_state.raw_items)} компаний. Переходите к обогащению!")
    else:
        st.error("❌ Ничего не найдено или проверьте API-ключи.")
    st.rerun()

if col_ai.button("🔍 ШАГ 2. Парсинг + AI", type=step2_type, disabled=not st.session_state.raw_items, use_container_width=True):
    st.session_state.stop_requested = False
    total = len(st.session_state.raw_items)
    log_message(f"🎯 Парсинг {total} компаний...")
    log_message(f"🤖 AI: {st.session_state.ai_provider} ({st.session_state.ai_model})")
    
    progress_bar = st.progress(0)
    stats_placeholder = st.empty()
    
    if sys.platform == 'win32':
        try: asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception: pass

    processed_data = []
    
    async def run_enrichment():
        count = 0
        async for result in enricher.batch_process(
            st.session_state.raw_items, 
            log_func=log_message, 
            use_ai=True,
            ai_provider=st.session_state.ai_provider,
            ai_model=st.session_state.ai_model
        ):
            if st.session_state.stop_requested: break
            
            count += 1
            processed_data.append(result)
            progress_bar.progress(count / total)
            stats_placeholder.info(f"📊 {count}/{total}")
        
        st.session_state.hunter_data = processed_data
        log_message("=" * 40)
        log_message(f"✅ ГОТОВО: {count} лидов")
    
    asyncio.run(run_enrichment())
    play_sound()
    st.success("✅ Парсинг + AI завершён!")

if col_stop.button("🛑 СТОП", use_container_width=True):
    st.session_state.stop_requested = True
    st.rerun()

# Таблица и логи
st.header("3. Результаты")
if st.session_state.hunter_data:
    df = pd.DataFrame(st.session_state.hunter_data)
    st.dataframe(df, hide_index=True, use_container_width=True)
    
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

with st.expander("📝 Технический лог"):
    st.code("\n".join(st.session_state.logs[::-1]))

# Footer
st.markdown("---")
st.markdown("**ЮгСпецСети | Охотник v3.0** | югспецсети.рф | t.me/Concreator")
