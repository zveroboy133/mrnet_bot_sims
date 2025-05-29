# Find SIMs

Программа для распознавания номеров SIM-карт на изображениях с использованием OpenCV и Tesseract OCR.

## Требования

- Python 3.x
- OpenCV (opencv-python)
- Tesseract OCR
- pytesseract
- Pillow (PIL)

## Установка

1. Установите Python зависимости:
```bash
pip install opencv-python pytesseract pillow
```

2. Установите Tesseract OCR:
- Windows: Скачайте и установите с [официального сайта](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`

## Использование

1. Поместите изображение с SIM-картами в директорию проекта
2. Укажите путь к изображению в `main_2.py`
3. Запустите скрипт:
```bash
python main_2.py
```

## Результаты

Программа создаст директорию `processing_steps` с промежуточными результатами обработки изображения и выведет найденные номера SIM-карт.