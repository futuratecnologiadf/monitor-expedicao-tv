@echo off
set IP_SERVER=192.168.1.3
set PYTHON_EXECUTABLE=C:\Users\Administrador\AppData\Local\Python\pythoncore-3.14-64\python.exe
cd "N:\monitor\EXPEDIÇÃO"
"%PYTHON_EXECUTABLE%" -m pip install -r requirements.txt
start "Monitor TV" "%PYTHON_EXECUTABLE%" -m streamlit run tv.py --server.address=%IP_SERVER% --browser.serverAddress=%IP_SERVER% --server.port=8501 --server.headless true
start "Monitor Gerente" "%PYTHON_EXECUTABLE%" -m streamlit run gerente.py --server.address=%IP_SERVER% --browser.serverAddress=%IP_SERVER% --server.port=8502 --server.headless true
exit