@echo off
chcp 65001 >nul
echo === Установка pygame ===
python -m pip install --upgrade pip
python -m pip install pygame
if errorlevel 1 (
  echo.
  echo Не удалось установить pygame. Скорее всего, Python слишком новый.
  echo Установи Python 3.12 с python.org и запусти этот файл снова.
  pause
  exit /b 1
)
echo === Запуск игры ===
python main.py
pause
