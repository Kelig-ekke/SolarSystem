@echo off
REM Solar System Simulator - Build Script for Windows
REM Автоматическая сборка проекта в исполняемый файл

echo Solar System Simulator - Сборка проекта
echo ===========================================

REM Проверка Python
py --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден. Установите Python 3.8 или выше.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('py --version') do set PYTHON_VERSION=%%i
echo Python найден: %PYTHON_VERSION%

REM Установка зависимостей
echo.
echo Установка зависимостей...
py -m pip install -r requirements.txt --quiet

py -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Установка PyInstaller...
    py -m pip install pyinstaller --quiet
)

echo Зависимости установлены

REM Очистка старых сборок
echo.
echo Очистка старых сборок...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul

REM Сборка проекта
echo.
echo Сборка проекта...
py -m PyInstaller build_config.spec

REM Проверка результата
if exist "dist\SolarSystemSimulator.exe" (
    echo.
    echo Сборка успешна!
    echo.
    echo Исполняемый файл находится в:
    echo    .\dist\SolarSystemSimulator.exe
    echo.
    echo Запуск:
    echo    .\dist\SolarSystemSimulator.exe
) else (
    echo.
    echo Ошибка при сборке!
    pause
    exit /b 1
)

pause
