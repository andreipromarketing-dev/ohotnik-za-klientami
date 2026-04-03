@echo off
cd /d "%~dp0"
echo ==========================================
echo Запуск приложения "Охотник за клиентами"
echo ==========================================
python -m streamlit run app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ОШИБКА] Не удалось запустить Streamlit. 
    echo Убедитесь, что Python установлен и зависимости установлены:
    echo pip install -r requirements.txt
    pause
)
