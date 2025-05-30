# Find SIMs

Проект для распознавания номеров SIM-карт на изображениях с использованием компьютерного зрения и OCR.

## Описание

Этот проект использует OpenCV и EasyOCR для:
1. Предобработки изображений
2. Поиска областей с текстом
3. Распознавания цифр в найденных областях

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/zveroboy133/find_sims.git
cd find_sims
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

1. Поместите изображение с SIM-картой в корневую директорию проекта
2. Запустите скрипт:
```bash
python main_2.py
```

3. Результаты обработки будут сохранены в директории `processing_steps`

## Структура проекта

- `main_2.py` - основной скрипт для обработки изображений
- `requirements.txt` - зависимости проекта
- `processing_steps/` - директория для сохранения промежуточных результатов
- `easyocr_models/` - директория для моделей EasyOCR

## Требования

- Python 3.8+
- OpenCV
- EasyOCR
- NumPy
- Pillow