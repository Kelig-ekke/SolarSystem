#!/bin/bash

# Solar System Simulator - Build Script
# Автоматическая сборка проекта в исполняемый файл

echo "Solar System Simulator - Сборка проекта"
echo "==========================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

echo "Python3 найден: $(python3 --version)"

# Установка зависимостей
echo ""
echo "Установка зависимостей..."
pip install -r requirements.txt --quiet

if ! pip show pyinstaller &> /dev/null; then
    echo "Установка PyInstaller..."
    pip install pyinstaller --quiet
fi

echo "Зависимости установлены"

# Очистка старых сборок
echo ""
echo "Очистка старых сборок..."
rm -rf build dist *.egg-info .spec 2>/dev/null

# Сборка проекта
echo ""
echo "Сборка проекта..."
pyinstaller build_config.spec

# Проверка результата
if [ -d "dist" ] && [ -f "dist/SolarSystemSimulator" ]; then
    echo ""
    echo "Сборка успешна!"
    echo ""
    echo "Исполняемый файл находится в:"
    echo "   ./dist/SolarSystemSimulator"
    echo ""
    echo "Запуск:"
    echo "   ./dist/SolarSystemSimulator"
else
    echo ""
    echo "Ошибка при сборке!"
    exit 1
fi
