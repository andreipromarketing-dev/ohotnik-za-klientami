import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime
import requests
import config
import io
import sys
import asyncio
import enricher
import search_providers
import streamlit.components.v1 as components

st.set_page_config(page_title="ЮгСпецСети | Охотник за клиентами", page_icon="🎯", layout="wide")

# CSS для анимации кнопок
st.markdown("""
<style>
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.6; }
    100% { opacity: 1; }
}
.stButton>button[data-baseweb="button"] {
    animation: pulse 1.5s ease-in-out infinite;
}
.stButton>button[data-baseweb="button"]:hover {
    animation: none;
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)

def play_sound():
    """Воспроизводит звуковое уведомление через JavaScript"""
    sound_html = """
    <script>
    try {
        var audioContext = new (window.AudioContext || window.webkitAudioContext)();
        var oscillator = audioContext.createOscillator();
        var gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch(e) { console.log('Audio error:', e); }
    </script>
    """
    components.html(sound_html, height=0)

st.title("🎯 Охотник за B2B-клиентами")
st.markdown("**Агентство:** [ЮгСпецСети](https://yugseti.ru) | Нейропродавец | Нейроассистент | AI для бизнеса")

# Инициализация состояний
if "logs" not in st.session_state:
    st.session_state.logs = []
if "hunter_data" not in st.session_state:
    st.session_state.hunter_data = [] 
if "raw_items" not in st.session_state:
    st.session_state.raw_items = []
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

def log_message(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")
    if len(st.session_state.logs) > 100:
        st.session_state.logs.pop(0)

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

try:
    from lm_studio_client import check_lm_studio
    if check_lm_studio():
        st.sidebar.success("✅ LM-Studio: Подключен")
    else:
        st.sidebar.warning("⚠️ LM-Studio: Недоступен (AI-анализ выключен)")
except:
    st.sidebar.warning("⚠️ LM-Studio: Не настроен")

# Блок выбора аудитории
st.header("1. Настройка поиска")

c1, c2, c3 = st.columns(3)
with c1:
    niche = st.selectbox("Категория бизнеса:", list(config.HUNTER_QUERIES.keys()))
    manual_niche = st.text_input("ИЛИ введите свою нишу:")
with c2:
    region = st.selectbox("Город:", list(config.REGION_COORDS.keys()))
    manual_city = st.text_input("ИЛИ введите город:")
with c3:
    limit = st.slider("Кол-во компаний:", 10, 500, 50, 10)

st.header("2. Управление")
if not config.SEARCHAPI_API_KEY:
    st.error("⚠️ **Внимание:** Не настроен SearchApi.io. Добавьте ключ в файл `.env`.")

col_start, col_ai, col_stop = st.columns([1.5, 1.5, 1])

if col_start.button("🚀 ШАГ 1. Поиск", type="primary", use_container_width=True):
    st.session_state.stop_requested = False
    st.session_state.raw_items = []
    st.session_state.hunter_data = []
    
    current_city = manual_city if manual_city else region
    
    if manual_niche:
        final_niches = [manual_niche]
    else:
        niche_val = config.HUNTER_QUERIES.get(niche, [])
        final_niches = niche_val if isinstance(niche_val, list) else [niche_val]
    
    log_message(f"🎯 Категория: {niche}")
    
    seen_names = set()
    results = []
    
    async def run_search():
        for q_niche in final_niches:
            if st.session_state.stop_requested: break
            query = f"{q_niche} {current_city}".strip()
            log_message(f"📡 Поиск: {query}...")
            
            batch = await search_providers.fetch_companies(query, limit)
            for item in batch:
                name = item.get('name', '').strip().lower()
                if name and name not in seen_names:
                    seen_names.add(name)
                    results.append(item)
            log_message(f"✅ Найдено уникальных: {len(results)}")
            if len(results) >= limit: break

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
        play_sound()
    else:
        st.error("❌ Ничего не найдено или проверьте API-ключи.")
    st.rerun()

if col_ai.button("🔍 ШАГ 2. Парсинг + AI", type="secondary", disabled=not st.session_state.raw_items, use_container_width=True):
    st.session_state.stop_requested = False
    total = len(st.session_state.raw_items)
    log_message(f"🎯 Парсинг {total} компаний...")
    log_message(f"🤖 AI-поиск ЛПР: ВКЛ")
    
    progress_bar = st.progress(0)
    stats_placeholder = st.empty()
    
    if sys.platform == 'win32':
        try: asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except: pass

    processed_data = []
    
    async def run_enrichment():
        count = 0
        async for result in enricher.batch_process(st.session_state.raw_items, log_func=log_message, use_ai=True):
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
st.markdown(f"**ЮгСпецСети | Охотник v3.0** | {config.AGENCY_CONTACT}")
