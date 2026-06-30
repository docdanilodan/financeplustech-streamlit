@echo off
cd /d "%~dp0"
echo ===========================================
echo FinancePlusTech Web App
echo ===========================================
echo Cartella corrente:
cd
echo.
echo Installazione dipendenze...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Avvio applicazione...
python -m streamlit run app.py
pause
