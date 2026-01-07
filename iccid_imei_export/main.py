#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт выгрузки ICCID:IMEI из Google Sheets

Этот скрипт читает данные из Google Sheets (лист SIMS) и создает CSV файлы
для различных операторов (МТС, Теле2, Билайн) в требуемых форматах.

АВТОР: Система автоматизации OTK Helper
ВЕРСИЯ: 1.0
"""

import os
import sys
import datetime
from pathlib import Path

# Импортируем GoogleSheetsProcessor из текущей директории
current_dir = Path(__file__).parent
# Добавляем текущую директорию в sys.path для импорта модулей
sys.path.insert(0, str(current_dir))

try:
    from google_sheets_processor import GoogleSheetsProcessor
except ImportError as e:
    print(f"[ОШИБКА] Не удалось импортировать GoogleSheetsProcessor: {e}")
    print(f"[ПОДСКАЗКА] Текущая директория: {current_dir}")
    print(f"[ПОДСКАЗКА] sys.path: {sys.path}")
    print(f"[ПОДСКАЗКА] Проверьте, что файл google_sheets_processor.py находится в: {current_dir}")
    sys.exit(1)


def find_credentials_file():
    """
    Ищет файл с учетными данными Google API
    
    Returns:
        Path: Путь к файлу credentials или None
    """
    # Определяем текущую директорию и родительскую
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    
    # Список возможных путей
    possible_paths = [
        script_dir / 'client_secret.json',
        script_dir / 'credentials.json',
        parent_dir / 'client_secret.json',
        parent_dir / 'credentials.json',
        parent_dir.parent / 'mrnet_ssh' / 'client_secret.json',
        parent_dir.parent / 'mrnet_ssh' / 'credentials.json',
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None


def export_iccid_imei():
    """
    Основная функция выгрузки ICCID:IMEI
    """
    print("=" * 60)
    print("    ВЫГРУЗКА ICCID : IMEI")
    print("=" * 60)
    
    # Ищем файл с учетными данными
    credentials_file = find_credentials_file()
    
    if not credentials_file:
        print(f"\n[ОШИБКА] Файл учетных данных не найден")
        print(f"[ПОДСКАЗКА] Ожидаемые пути:")
        script_dir = Path(__file__).parent
        parent_dir = script_dir.parent
        for path in [
            script_dir / 'client_secret.json',
            script_dir / 'credentials.json',
            parent_dir / 'client_secret.json',
            parent_dir / 'credentials.json',
            parent_dir.parent / 'mrnet_ssh' / 'client_secret.json',
        ]:
            print(f"    - {path}")
        return False
    
    print(f"\n[ИНФО] Используем файл учетных данных: {credentials_file}")
    
    try:
        # Создаем экземпляр процессора
        abs_credentials_file = str(credentials_file.absolute())
        token_file = credentials_file.parent / 'token.json'
        abs_token_file = str(token_file.absolute()) if token_file.exists() else None
        
        processor = GoogleSheetsProcessor(
            credentials_file=abs_credentials_file,
            token_file=abs_token_file
        )
        
        print("\n[СКАНИРОВАНИЕ] Читаем данные из таблицы SIMS...")
        
        # Получаем все данные из таблицы
        all_values = processor.worksheet.get_all_values()
        
        if not all_values or len(all_values) < 2:
            print("\n[ОШИБКА] Таблица пуста или содержит только заголовки")
            return False
        
        # Первая строка - заголовки
        headers = all_values[0]
        
        # Находим индексы нужных столбцов
        imei_col_idx = None
        iccid_col_idx = None
        
        for idx, header in enumerate(headers):
            header_lower = str(header).strip().lower()
            if 'imei' in header_lower:
                imei_col_idx = idx
            if idx == 4:  # Столбец E (индекс 4, так как A=0, B=1, C=2, D=3, E=4)
                iccid_col_idx = idx
        
        # Проверяем, что нашли столбец IMEI
        if imei_col_idx is None:
            print("\n[ОШИБКА] Не найден столбец 'IMEI' в таблице")
            print(f"[ИНФО] Найденные заголовки: {headers}")
            return False
        
        if iccid_col_idx is None:
            print("\n[ОШИБКА] Не найден столбец E (ICCID) в таблице")
            return False
        
        print(f"[ИНФО] Столбец IMEI найден: колонка {chr(65 + imei_col_idx)} (индекс {imei_col_idx})")
        print(f"[ИНФО] Столбец ICCID: колонка E (индекс {iccid_col_idx})")
        
        # Определяем операторов по префиксам ICCID
        operators = {
            'МТС': '8970101',
            'Мегафон': '8970102',
            'Теле2': '8970120',
            'Билайн': '8970199'
        }
        
        # Собираем данные по операторам
        operator_data = {op: [] for op in operators.keys()}
        unknown_operator = []
        
        # Сканируем начиная со второй строки (индекс 1)
        processed_count = 0
        found_count = 0
        
        for row_idx in range(1, len(all_values)):
            row = all_values[row_idx]
            
            # Получаем IMEI из столбца
            if len(row) > imei_col_idx:
                imei_value = str(row[imei_col_idx]).strip()
                
                # Проверяем, что IMEI содержит набор цифр
                if imei_value and any(c.isdigit() for c in imei_value):
                    # Извлекаем только цифры из IMEI
                    imei_digits = ''.join(filter(str.isdigit, imei_value))
                    
                    if imei_digits:  # Если есть хотя бы одна цифра
                        # Получаем ICCID из столбца E
                        if len(row) > iccid_col_idx:
                            iccid_value = str(row[iccid_col_idx]).strip()
                            iccid_digits = ''.join(filter(str.isdigit, iccid_value))
                            
                            if iccid_digits:
                                # Определяем оператора по префиксу ICCID
                                operator_found = None
                                for op_name, prefix in operators.items():
                                    if iccid_digits.startswith(prefix):
                                        operator_found = op_name
                                        break
                                
                                if operator_found:
                                    operator_data[operator_found].append({
                                        'iccid': iccid_digits,
                                        'imei': imei_digits
                                    })
                                    found_count += 1
                                else:
                                    unknown_operator.append({
                                        'iccid': iccid_digits,
                                        'imei': imei_digits,
                                        'row': row_idx + 1
                                    })
            
            processed_count += 1
        
        print(f"\n[СТАТИСТИКА] Обработано строк: {processed_count}")
        print(f"[СТАТИСТИКА] Найдено записей с IMEI и ICCID: {found_count}")
        
        # Выводим статистику по операторам
        print("\n" + "=" * 60)
        print("    СТАТИСТИКА ПО ОПЕРАТОРАМ")
        print("=" * 60)
        for op_name, data_list in operator_data.items():
            print(f"    {op_name}: {len(data_list)} записей")
        if unknown_operator:
            print(f"    Неизвестный оператор: {len(unknown_operator)} записей")
        
        # Создаем директорию для экспорта
        script_dir = Path(__file__).parent
        output_dir = script_dir / 'exports'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Обрабатываем данные для МТС
        if operator_data['МТС']:
            print("\n" + "=" * 60)
            print("    СОЗДАНИЕ CSV ФАЙЛА ДЛЯ МТС")
            print("=" * 60)
            
            csv_filename = output_dir / f'MTS_ICCID_IMEI_{timestamp}.csv'
            
            try:
                with open(csv_filename, 'w', encoding='utf-8') as f:
                    # Записываем заголовок первой строкой
                    f.write("ICCID;IMEI\n")
                    for item in operator_data['МТС']:
                        f.write(f"{item['iccid']};{item['imei']}\n")
                
                print(f"\n[УСПЕХ] CSV файл создан: {csv_filename}")
                print(f"[ИНФО] Записей в файле: {len(operator_data['МТС'])}")
                
                # Показываем первые несколько записей как пример
                print("\n[ПРИМЕР] Первые 5 записей:")
                for i, item in enumerate(operator_data['МТС'][:5], 1):
                    print(f"    {i}. {item['iccid']};{item['imei']}")
                
            except Exception as e:
                print(f"\n[ОШИБКА] Не удалось создать CSV файл: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("\n[ИНФО] Нет данных для МТС")
        
        # Обрабатываем данные для Теле2
        if operator_data['Теле2']:
            print("\n" + "=" * 60)
            print("    СОЗДАНИЕ CSV ФАЙЛА ДЛЯ ТЕЛЕ2")
            print("=" * 60)
            
            csv_filename = output_dir / f'Теле2_{timestamp}.csv'
            
            try:
                with open(csv_filename, 'w', encoding='utf-8') as f:
                    # Записываем заголовок первой строкой
                    f.write("ICCID;IMEI\n")
                    for item in operator_data['Теле2']:
                        f.write(f"{item['iccid']};{item['imei']}\n")
                
                print(f"\n[УСПЕХ] CSV файл создан: {csv_filename}")
                print(f"[ИНФО] Записей в файле: {len(operator_data['Теле2'])}")
                
                # Показываем первые несколько записей как пример
                print("\n[ПРИМЕР] Первые 5 записей:")
                for i, item in enumerate(operator_data['Теле2'][:5], 1):
                    print(f"    {i}. {item['iccid']};{item['imei']}")
                
            except Exception as e:
                print(f"\n[ОШИБКА] Не удалось создать CSV файл: {e}")
                import traceback
                traceback.print_exc()
        
        # Обрабатываем данные для Билайна
        if operator_data['Билайн']:
            print("\n" + "=" * 60)
            print("    СОЗДАНИЕ CSV ФАЙЛОВ ДЛЯ БИЛАЙНА")
            print("=" * 60)
            
            # Создаем первый файл: список ICCID (без заголовка)
            iccid_filename = output_dir / f'Билайн_ICCID_{timestamp}.csv'
            
            # Создаем второй файл: список IMEI в формате type;value
            imei_filename = output_dir / f'Билайн_IMEI_{timestamp}.csv'
            
            try:
                # Создаем файл с ICCID
                with open(iccid_filename, 'w', encoding='utf-8') as f:
                    for item in operator_data['Билайн']:
                        f.write(f"{item['iccid']}\n")
                
                # Создаем файл с IMEI в формате type;value
                with open(imei_filename, 'w', encoding='utf-8') as f:
                    for item in operator_data['Билайн']:
                        f.write(f"IMEI;{item['imei']}\n")
                
                print(f"\n[УСПЕХ] CSV файлы созданы:")
                print(f"    ICCID файл: {iccid_filename}")
                print(f"    IMEI файл: {imei_filename}")
                print(f"[ИНФО] Записей в файлах: {len(operator_data['Билайн'])}")
                
                # Показываем первые несколько записей как пример
                print("\n[ПРИМЕР] Первые 3 записи:")
                for i, item in enumerate(operator_data['Билайн'][:3], 1):
                    print(f"    {i}. ICCID: {item['iccid']}, IMEI: {item['imei']}")
                
            except Exception as e:
                print(f"\n[ОШИБКА] Не удалось создать CSV файлы: {e}")
                import traceback
                traceback.print_exc()
        
        # Заглушка для Мегафона
        if operator_data['Мегафон']:
            print(f"\n[Мегафон] Найдено {len(operator_data['Мегафон'])} записей")
            print(f"    [ЗАГЛУШКА] Функция экспорта для Мегафон находится в разработке")
            print(f"    [ПРИМЕР] Первая запись: ICCID={operator_data['Мегафон'][0]['iccid']}, IMEI={operator_data['Мегафон'][0]['imei']}")
        
        if unknown_operator:
            print(f"\n[ВНИМАНИЕ] Найдено {len(unknown_operator)} записей с неизвестным оператором")
            print("    [ПРИМЕР] Первые 3 записи:")
            for i, item in enumerate(unknown_operator[:3], 1):
                print(f"        {i}. Строка {item['row']}: ICCID={item['iccid']}, IMEI={item['imei']}")
        
        print("\n" + "=" * 60)
        print("    ВЫГРУЗКА ЗАВЕРШЕНА")
        print("=" * 60)
        print(f"[ИНФО] Файлы сохранены в директории: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n[ОШИБКА] Ошибка при выгрузке данных: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = export_iccid_imei()
    sys.exit(0 if success else 1)

