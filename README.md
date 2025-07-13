# Find SIMs

## Настройка Google API

Для работы с Google Sheets необходимо настроить OAuth 2.0:

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Google Sheets API и Google Drive API
3. Создайте учетные данные OAuth 2.0:
   - Тип приложения: Desktop app
   - Скачайте JSON-файл с учетными данными
   - Переименуйте файл в `client_secret.json`
   - Поместите файл в корневую директорию проекта

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Скопируйте пример конфигурации:
```bash
cp client_secret.example.json client_secret.json
```

3. Замените значения в `client_secret.json` на ваши учетные данные из Google Cloud Console

## Использование

```python
from google_sheets_processor import GoogleSheetsProcessor

# Создание экземпляра процессора
processor = GoogleSheetsProcessor()

# Поиск по телефону
result = processor.search_by_phone("+79001234567")
if result:
    print("Найдена запись:", result)

# Поиск по имени
results = processor.search_by_name("Иван")
if results:
    print("Найдены записи:", results)
```

При первом запуске откроется браузер для авторизации в Google.

tmp_easyocr.py
- читает фото симкарт
- на выходе отдает необработанные номера ICCID