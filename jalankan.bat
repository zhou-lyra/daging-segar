@echo off
rem Peluncur BeefFresh untuk Windows.
rem Membuat .venv bila belum ada, lalu MEMERIKSA isinya (PySide6 + pyserial) dan memasangnya bila kurang.
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo Membuat lingkungan Python .venv ...
  for %%V in (3.13 3.12 3.11 3.10 3) do if not exist .venv\Scripts\python.exe py -%%V -m venv .venv >nul 2>&1
)
if not exist .venv\Scripts\python.exe goto :nopython

.venv\Scripts\python -c "import serial, PySide6" >nul 2>&1
if errorlevel 1 (
  echo Memasang PySide6 dan pyserial ^(sekitar 260 MB, butuh internet^). Mohon tunggu...
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -r requirements.txt
  if errorlevel 1 goto :gagal
)

.venv\Scripts\python pengambil_data_qt.py %*
if errorlevel 1 pause
exit /b

:nopython
echo.
echo Python 3 tidak ditemukan. Pasang Python 3.12 atau 3.13 dari python.org,
echo centang "Add python.exe to PATH" saat memasang, lalu jalankan file ini lagi.
pause
exit /b 1

:gagal
echo.
echo Pemasangan pustaka GAGAL ^(lihat pesan di atas^). Penyebab yang umum:
echo  - tidak ada internet / unduhan terputus: jalankan file ini lagi
echo  - Python terlalu baru: pakai Python 3.12 atau 3.13, lalu hapus folder .venv dan ulangi
pause
exit /b 1
