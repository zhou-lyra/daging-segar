@echo off
rem Peluncur BeefFresh untuk Windows. Pertama kali: membuat .venv dan memasang PySide6 + pyserial (butuh internet, +-260 MB).
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv || (echo Python 3 belum terpasang. Pasang dari python.org lalu centang "Add python.exe to PATH". & pause & exit /b 1)
  .venv\Scripts\python -m pip install -r requirements.txt || (echo Pemasangan gagal. & pause & exit /b 1)
)
.venv\Scripts\python pengambil_data_qt.py %*
if errorlevel 1 pause
