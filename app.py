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
LOGO_PATH = Path(r"E:\СОЦИТУД\AI-Эксперт\ЮгСпецСети\Фотошопное\Иконки\150.jpg")

def load_custom_apis():
    """Загружает кастомные API из файла"""
    if API_STORE_FILE.exists():
        try:
            decoded = base64.b64decode(API_STORE_FILE.read_text().encode())
            return json.loads(decoded.decode())
        except:
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
# CSS С ДВУМЯ ТЕМАМИ: ТЁМНАЯ (#012F46) и СВЕТЛАЯ (#F8F9FA)
# ============================================================================

st.markdown("""
<script>
window.addEventListener('DOMContentLoaded', function() {
    // Функция определения темы по цвету фона
    function detectTheme() {
        const app = document.querySelector('.stApp');
        if (!app) return 'dark';
        
        const bg = getComputedStyle(app).backgroundColor;
        // Streamlit в тёмном режиме: rgb(1, 47, 70) или rgb(18, 46, 70)
        // Streamlit в светлом режиме: rgb(248, 249, 250) или rgb(255, 255, 255)
        if (bg.includes('1, 47, 70') || bg.includes('18, 46, 70') || bg.includes('2, 46, 70')) {
            return 'dark';
        }
        return 'light';
    }
    
    // Установка атрибута темы
    function setThemeAttr() {
        const theme = detectTheme();
        document.querySelector('.stApp').setAttribute('data-theme', theme);
    }
    
    // Ограничение ширины меню - привязка к toolbar справа
    function fixMenuWidth() {
        document.querySelectorAll('[data-baseweb="menu"], [role="menu"], [data-baseweb="popover"]').forEach(function(el) {
            el.style.maxWidth = '220px';
            el.style.minWidth = '180px';
            el.style.width = 'auto';
            el.style.position = 'absolute';
            el.style.top = '100%';
            el.style.left = 'auto';
            el.style.right = '0';
            el.style.transform = 'none';
        });
    }
    
    // Запускаем при загрузке
    setTimeout(setThemeAttr, 300);
    setInterval(setThemeAttr, 2000);
    setTimeout(fixMenuWidth, 500);
    
    // Следим за кликами - исправляем меню при открытии
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-testid="stToolbar"]') || e.target.closest('button[aria-haspopup]')) {
            setTimeout(fixMenuWidth, 50);
            setTimeout(fixMenuWidth, 200);
            setTimeout(fixMenuWidth, 500);
        }
    });
    
    // Следим за кликами на кнопках темы
    const observer = new MutationObserver(setThemeAttr);
    observer.observe(document.body, { attributes: true, childList: true, subtree: true });
});
</script>

<style>
/* ============================================================================
[data-theme="dark"] - ТЁМНАЯ ТЕМА (#012F46)
============================================================================ */
.stApp[data-theme="dark"] {
    background: #012F46 !important;
}
.stApp[data-theme="dark"] * {
    color: #ffffff !important;
}

/* Основной контент */
.stApp[data-theme="dark"] .main {
    background: #012F46 !important;
}

/* Sidebar */
.stApp[data-theme="dark"] section[data-testid="stSidebar"] {
    background: #013a5c !important;
}
.stApp[data-theme="dark"] section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
.stApp[data-theme="dark"] section[data-testid="stSidebar"] .stMarkdown {
    color: #b0c4d4 !important;
}

/* Кнопки ВСЕ */
.stApp[data-theme="dark"] button,
.stApp[data-theme="dark"] .stButton > button,
.stApp[data-theme="dark"] [data-testid="stBaseButton-secondary"],
.stApp[data-theme="dark"] [data-testid="stBaseButton-primary"],
.stApp[data-theme="dark"] button p,
.stApp[data-theme="dark"] button span {
    color: #0D1117 !important;
    background: #E8F9EE !important;
    border: none !important;
}
.stApp[data-theme="dark"] button:hover,
.stApp[data-theme="dark"] .stButton > button:hover {
    background: #d4f4e3 !important;
}

/* Ввод текста (Inputs) */
.stApp[data-theme="dark"] input,
.stApp[data-theme="dark"] .stTextInput > div > div > input,
.stApp[data-theme="dark"] textarea,
.stApp[data-theme="dark"] .stTextArea > div > div > textarea {
    background: #024d82 !important;
    color: #ffffff !important;
    border: 1px solid #024d82 !important;
}
.stApp[data-theme="dark"] input::placeholder,
.stApp[data-theme="dark"] textarea::placeholder {
    color: #b0c4d4 !important;
}

/* Select/Selectbox */
.stApp[data-theme="dark"] .stSelectbox > div > div,
.stApp[data-theme="dark"] [data-baseweb="select"] {
    background: #024d82 !important;
    color: #ffffff !important;
    border: 1px solid #024d82 !important;
}
.stApp[data-theme="dark"] [data-baseweb="select"] * {
    color: #ffffff !important;
}

/* Radio buttons */
.stApp[data-theme="dark"] .stRadio > div,
.stApp[data-theme="dark"] [role="radiogroup"] {
    color: #ffffff !important;
}
.stApp[data-theme="dark"] .stRadio div[role="radiogroup"] label:has(input:checked) {
    background: #E8F9EE !important;
    color: #0D1117 !important;
    border-radius: 4px;
}
.stApp[data-theme="dark"] .stRadio div[role="radiogroup"] label {
    color: #b0c4d4 !important;
}

/* Checkbox */
.stApp[data-theme="dark"] .stCheckbox > label,
.stApp[data-theme="dark"] [role="checkbox"] {
    color: #ffffff !important;
}

/* Expanders/Details */
.stApp[data-theme="dark"] .streamlit-expander,
.stApp[data-theme="dark"] details {
    background: #013a5c !important;
    border: 1px solid #024d82 !important;
    border-radius: 4px;
}
.stApp[data-theme="dark"] .streamlit-expander summary,
.stApp[data-theme="dark"] details summary {
    color: #ffffff !important;
}
.stApp[data-theme="dark"] .streamlit-expander summary:hover,
.stApp[data-theme="dark"] details summary:hover {
    background: #024d82 !important;
}

/* Slider */
.stApp[data-theme="dark"] .stSlider [role="slider"] {
    background: #E8F9EE !important;
}
.stApp[data-theme="dark"] .stSlider .stMarkdown {
    color: #b0c4d4 !important;
}

/* Progress bar */
.stApp[data-theme="dark"] .stProgress > div > div {
    background: #E8F9EE !important;
}
.stApp[data-theme="dark"] .stProgress > div > div > div {
    background: #E8F9EE !important;
}

/* Spinner */
.stApp[data-theme="dark"] .stSpinner > div {
    border: 3px solid #013a5c !important;
    border-top: 3px solid #E8F9EE !important;
}

/* Metric */
.stApp[data-theme="dark"] [data-testid="stMetricValue"] {
    color: #E8F9EE !important;
}
.stApp[data-theme="dark"] [data-testid="stMetricLabel"] {
    color: #b0c4d4 !important;
}

/* Dataframe/Table */
.stApp[data-theme="dark"] .stDataFrame,
.stApp[data-theme="dark"] [data-testid="stDataFrame"] {
    background: #013a5c !important;
}
.stApp[data-theme="dark"] .stDataFrame thead th,
.stApp[data-theme="dark"] [data-testid="stDataFrame"] thead th {
    background: #024d82 !important;
    color: #ffffff !important;
}

/* Download button */
.stApp[data-theme="dark"] .stDownloadButton > button {
    color: #0D1117 !important;
    background: #E8F9EE !important;
}

/* Streamlit Header/Toolbar menu (три точки) */
.stApp[data-theme="dark"] [data-testid="stHeader"],
.stApp[data-theme="dark"] header {
    background: #012F46 !important;
}
.stApp[data-theme="dark"] [data-testid="stToolbar"],
.stApp[data-theme="dark"] header button,
.stApp[data-theme="dark"] [role="menubutton"],
.stApp[data-theme="dark"] [data-testid="stToolbar"] button {
    color: #ffffff !important;
}
.stApp[data-theme="dark"] [data-testid="stToolbar"] button:hover {
    background: #024d82 !important;
}

/* Dropdown menus, popover */
.stApp[data-theme="dark"] [data-baseweb="popover"],
.stApp[data-theme="dark"] [data-baseweb="menu"],
.stApp[data-theme="dark"] [role="menu"],
.stApp[data-theme="dark"] [role="menubar"],
.stApp[data-theme="dark"] div[role="menu"],
.stApp[data-theme="dark"] div[role="dialog"] {
    background: #012F46 !important;
    border: 1px solid #024d82 !important;
    width: 180px !important;
    min-width: 180px !important;
    max-width: 180px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}
.stApp[data-theme="dark"] [data-baseweb="menu"] *,
.stApp[data-theme="dark"] [role="menu"] *,
.stApp[data-theme="dark"] [role="menuitem"] {
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
.stApp[data-theme="dark"] [data-baseweb="menu"] li:hover,
.stApp[data-theme="dark"] [data-baseweb="menu"] button:hover,
.stApp[data-theme="dark"] [role="menuitem"]:hover,
.stApp[data-theme="dark"] [role="menu"] li:hover {
    background: #024d82 !important;
    color: #ffffff !important;
}

/* Divider */
.stApp[data-theme="dark"] hr {
    border-color: #024d82 !important;
}

/* Streamlit alerts/messages */
.stApp[data-theme="dark"] .stSuccess {
    background: #013a5c !important;
    color: #E8F9EE !important;
}
.stApp[data-theme="dark"] .stError {
    background: #5c1a01 !important;
    color: #ff9999 !important;
}
.stApp[data-theme="dark"] .stWarning {
    background: #5c4a01 !important;
    color: #ffeb99 !important;
}
.stApp[data-theme="dark"] .stInfo {
    background: #013a5c !important;
    color: #99ccff !important;
}

/* ============================================================================
[data-theme="light"] - СВЕТЛАЯ ТЕМА (#F8F9FA)
============================================================================ */
.stApp[data-theme="light"] {
    background: #F8F9FA !important;
}
.stApp[data-theme="light"] * {
    color: #0D1117 !important;
}

/* Основной контент */
.stApp[data-theme="light"] .main {
    background: #F8F9FA !important;
}

/* Sidebar */
.stApp[data-theme="light"] section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #CED4DA !important;
}
.stApp[data-theme="light"] section[data-testid="stSidebar"] * {
    color: #0D1117 !important;
}
.stApp[data-theme="light"] section[data-testid="stSidebar"] .stMarkdown {
    color: #2C3339 !important;
}

/* Кнопки ВСЕ */
.stApp[data-theme="light"] button,
.stApp[data-theme="light"] .stButton > button,
.stApp[data-theme="light"] [data-testid="stBaseButton-secondary"],
.stApp[data-theme="light"] [data-testid="stBaseButton-primary"],
.stApp[data-theme="light"] button p,
.stApp[data-theme="light"] button span {
    color: #ffffff !important;
    background: #012F46 !important;
    border: none !important;
}
.stApp[data-theme="light"] button:hover,
.stApp[data-theme="light"] .stButton > button:hover {
    background: #024d82 !important;
}

/* Ввод текста (Inputs) */
.stApp[data-theme="light"] input,
.stApp[data-theme="light"] .stTextInput > div > div > input,
.stApp[data-theme="light"] textarea,
.stApp[data-theme="light"] .stTextArea > div > div > textarea {
    background: #FFFFFF !important;
    color: #0D1117 !important;
    border: 1px solid #CED4DA !important;
}
.stApp[data-theme="light"] input::placeholder,
.stApp[data-theme="light"] textarea::placeholder {
    color: #6c757d !important;
}

/* Select/Selectbox */
.stApp[data-theme="light"] .stSelectbox > div > div,
.stApp[data-theme="light"] [data-baseweb="select"] {
    background: #FFFFFF !important;
    color: #0D1117 !important;
    border: 1px solid #CED4DA !important;
}
.stApp[data-theme="light"] [data-baseweb="select"] * {
    color: #0D1117 !important;
}

/* Radio buttons */
.stApp[data-theme="light"] .stRadio > div,
.stApp[data-theme="light"] [role="radiogroup"] {
    color: #0D1117 !important;
}
.stApp[data-theme="light"] .stRadio div[role="radiogroup"] label:has(input:checked) {
    background: #012F46 !important;
    color: #ffffff !important;
    border-radius: 4px;
}
.stApp[data-theme="light"] .stRadio div[role="radiogroup"] label {
    color: #2C3339 !important;
}

/* Checkbox */
.stApp[data-theme="light"] .stCheckbox > label,
.stApp[data-theme="light"] [role="checkbox"] {
    color: #0D1117 !important;
}

/* Expanders/Details */
.stApp[data-theme="light"] .streamlit-expander,
.stApp[data-theme="light"] details {
    background: #FFFFFF !important;
    border: 1px solid #CED4DA !important;
    border-radius: 4px;
}
.stApp[data-theme="light"] .streamlit-expander summary,
.stApp[data-theme="light"] details summary {
    color: #0D1117 !important;
}
.stApp[data-theme="light"] .streamlit-expander summary:hover,
.stApp[data-theme="light"] details summary:hover {
    background: #F8F9FA !important;
}

/* Slider */
.stApp[data-theme="light"] .stSlider [role="slider"] {
    background: #012F46 !important;
}
.stApp[data-theme="light"] .stSlider .stMarkdown {
    color: #2C3339 !important;
}

/* Progress bar */
.stApp[data-theme="light"] .stProgress > div > div {
    background: #012F46 !important;
}
.stApp[data-theme="light"] .stProgress > div > div > div {
    background: #012F46 !important;
}

/* Spinner */
.stApp[data-theme="light"] .stSpinner > div {
    border: 3px solid #F8F9FA !important;
    border-top: 3px solid #012F46 !important;
}

/* Metric */
.stApp[data-theme="light"] [data-testid="stMetricValue"] {
    color: #012F46 !important;
}
.stApp[data-theme="light"] [data-testid="stMetricLabel"] {
    color: #2C3339 !important;
}

/* Dataframe/Table */
.stApp[data-theme="light"] .stDataFrame,
.stApp[data-theme="light"] [data-testid="stDataFrame"] {
    background: #FFFFFF !important;
}
.stApp[data-theme="light"] .stDataFrame thead th,
.stApp[data-theme="light"] [data-testid="stDataFrame"] thead th {
    background: #F8F9FA !important;
    color: #0D1117 !important;
}

/* Download button */
.stApp[data-theme="light"] .stDownloadButton > button {
    color: #ffffff !important;
    background: #012F46 !important;
}

/* Streamlit Header/Toolbar menu (три точки) */
.stApp[data-theme="light"] [data-testid="stHeader"],
.stApp[data-theme="light"] header {
    background: #F8F9FA !important;
}
.stApp[data-theme="light"] [data-testid="stToolbar"],
.stApp[data-theme="light"] header button,
.stApp[data-theme="light"] [role="menubutton"],
.stApp[data-theme="light"] [data-testid="stToolbar"] button {
    color: #0D1117 !important;
}
.stApp[data-theme="light"] [data-testid="stToolbar"] button:hover {
    background: #E8F9EE !important;
}

/* Dropdown menus, popover */
.stApp[data-theme="light"] [data-baseweb="popover"],
.stApp[data-theme="light"] [data-baseweb="menu"],
.stApp[data-theme="light"] [role="menu"],
.stApp[data-theme="light"] [role="menubar"],
.stApp[data-theme="light"] div[role="menu"],
.stApp[data-theme="light"] div[role="dialog"] {
    background: #FFFFFF !important;
    border: 1px solid #CED4DA !important;
    width: 180px !important;
    min-width: 180px !important;
    max-width: 180px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}
.stApp[data-theme="light"] [data-baseweb="menu"] *,
.stApp[data-theme="light"] [role="menu"] *,
.stApp[data-theme="light"] [role="menuitem"] {
    color: #0D1117 !important;
    background: #FFFFFF !important;
    width: 100% !important;
    max-width: 180px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    display: block !important;
    box-sizing: border-box !important;
}
.stApp[data-theme="light"] [data-baseweb="menu"] li:hover,
.stApp[data-theme="light"] [data-baseweb="menu"] button:hover,
.stApp[data-theme="light"] [role="menuitem"]:hover,
.stApp[data-theme="light"] [role="menu"] li:hover {
    background: #E8F9EE !important;
    color: #0D1117 !important;
}

/* Divider */
.stApp[data-theme="light"] hr {
    border-color: #CED4DA !important;
}

/* Streamlit alerts/messages */
.stApp[data-theme="light"] .stSuccess {
    background: #d4edda !important;
    color: #155724 !important;
}
.stApp[data-theme="light"] .stError {
    background: #f8d7da !important;
    color: #721c24 !important;
}
.stApp[data-theme="light"] .stWarning {
    background: #fff3cd !important;
    color: #856404 !important;
}
.stApp[data-theme="light"] .stInfo {
    background: #d1ecf1 !important;
    color: #0c5460 !important;
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

# Логотип в боковой панели (в самом верху)
col_logo1, col_logo2, col_logo3 = st.sidebar.columns([1, 2, 1])
if LOGO_PATH.exists():
    try:
        img = Image.open(LOGO_PATH)
        col_logo2.image(img, width=120)
    except Exception as e:
        col_logo2.caption("ЮгСпецСети")
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

# Переключатели (чекпоинты) для выбора API
if st.session_state.custom_apis:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Выбор активных API")
    
    # Инициализировать состояние чекпоинтов
    if "api_checkboxes" not in st.session_state:
        st.session_state.api_checkboxes = {name: False for name in st.session_state.custom_apis}
    
    # Чекпоинты для Поиска (синий)
    st.sidebar.markdown("**🔍 Для поиска:**")
    for name, api_data in st.session_state.custom_apis.items():
        if api_data['type'] == 'search':
            checked = st.sidebar.checkbox(f"✅ {name}", key=f"chk_search_{name}")
            if checked:
                st.session_state.selected_search_api = name
    
    # Чекпоинты для LLM (фиолетовый)
    st.sidebar.markdown("**🤖 Для обогащения:**")
    for name, api_data in st.session_state.custom_apis.items():
        if api_data['type'] == 'llm':
            checked = st.sidebar.checkbox(f"✅ {name}", key=f"chk_llm_{name}")
            if checked:
                st.session_state.selected_llm_api = name
    
    # Подписи
    st.sidebar.caption("🔍 - для поиска | 🤖 - для AI обогащения")

try:
    from lm_studio_client import check_lm_studio, get_available_models as get_lm_models
    from groq_client import check_groq, get_available_models as get_groq_models
    from unclose_client import check_unclose, get_available_models as get_unclose_models
    
    if check_lm_studio():
        st.sidebar.success("✅ LM-Studio: Подключен")
    if check_groq():
        st.sidebar.success("✅ Groq: Подключен")
    if check_unclose():
        st.sidebar.success("✅ UncloseAI: Подключен")
except:
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
            time.sleep(1)
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
    if ai_provider == "LM Studio":
        lm_models = get_lm_models()
        if lm_models:
            ai_model = st.selectbox("Модель:", lm_models, help="Выберите модель из LM Studio")
        else:
            ai_model = st.selectbox("Модель:", ["Модели не найдены"], disabled=True)
    elif ai_provider == "Groq":
        groq_models = get_groq_models()
        model_options = [(k, v) for k, v in groq_models.items()]
        model_labels = [f"{v} ({k})" for k, v in groq_models.items()]
        selected_idx = st.selectbox(
            "Модель:",
            range(len(model_labels)),
            format_func=lambda i: model_labels[i]
        )
        ai_model = model_options[selected_idx][0]
        st.caption("Лимит: 30 req/min, 40k токенов/мин")
    else:  # UncloseAI
        unclose_models = get_unclose_models()
        model_options = [(k, v) for k, v in unclose_models.items()]
        model_labels = [f"{v} ({k})" for k, v in unclose_models.items()]
        selected_idx = st.selectbox(
            "Модель:",
            range(len(model_labels)),
            format_func=lambda i: model_labels[i]
        )
        ai_model = model_options[selected_idx][0]
        st.caption("Безлимит, не требует API ключа")

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
    
    # Для кастомной ниши - используем как есть
    if manual_niche.strip():
        final_niches = [manual_niche.strip()]
    else:
        niche_val = config.HUNTER_QUERIES.get(niche, [])
        final_niches = niche_val if isinstance(niche_val, list) else [niche_val]
    
    log_message(f"🎯 Категория: {current_niche}")
    log_message(f"📝 Ниши для поиска: {final_niches}")
    
    seen_names = set()
    results = []
    
    # Placeholder для live-лога
    log_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    def live_log(msg):
        log_message(msg)
        log_placeholder.info(msg)
    
    async def run_search():
        for i, q_niche in enumerate(final_niches):
            if st.session_state.stop_requested: break
            query = f"{q_niche} {current_city}".strip()
            live_log(f"📡 Поиск: {query}...")
            progress_bar.progress((i + 1) / len(final_niches))
            
            batch = await search_providers.fetch_companies(query, limit, log_func=live_log)
            for item in batch:
                name = item.get('name', '').strip().lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    results.append(item)
            live_log(f"✅ Найдено уникальных: {len(results)}")
            if len(results) >= limit: break
        
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
        except: pass

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
