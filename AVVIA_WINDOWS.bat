@echo off
echo ===========================================
echo FinancePlusTech Web App
echo ===========================================
echo Installazione dipendenze...
pip install -r requirements.txt
echo Avvio applicazione...
streamlit run app.py
pause
