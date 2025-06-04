import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pandas as pd
from typing import List, Dict, Optional, Union

class GoogleSheetsProcessor:
    def __init__(self, credentials_file: str = 'client_secret.json'):
        """
        Инициализация процессора Google таблиц с использованием OAuth 2.0
        
        Args:
            credentials_file (str): Путь к файлу с учетными данными OAuth 2.0
        """
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
                      'https://www.googleapis.com/auth/drive']
        self.credentials_file = credentials_file
        self.creds = None
        self.spreadsheet_id = '1nx2QSynzcvt_gOb8gsC0l6Zs7nb7V_x-19kOLx93-WI'
        
        # Проверяем наличие сохраненных учетных данных
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # Если нет действительных учетных данных, запрашиваем новые
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Сохраняем учетные данные для следующего запуска
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        self.worksheet = self.spreadsheet.worksheet('SIMS')  # Замените на нужный лист

    def search_by_phone(self, phone: str) -> Optional[Dict]:
        """
        Поиск записи по номеру телефона
        
        Args:
            phone (str): Номер телефона для поиска
            
        Returns:
            Optional[Dict]: Словарь с данными найденной записи или None, если запись не найдена
        """
        try:
            # Получаем все данные из таблицы
            data = self.worksheet.get_all_records()
            
            # Ищем запись с указанным номером телефона
            for record in data:
                if str(record.get('phone', '')).strip() == str(phone).strip():
                    return record
            return None
        except Exception as e:
            print(f"Ошибка при поиске по телефону: {e}")
            return None

    def search_by_name(self, name: str) -> List[Dict]:
        """
        Поиск записей по имени
        
        Args:
            name (str): Имя для поиска
            
        Returns:
            List[Dict]: Список словарей с найденными записями
        """
        try:
            #headers = ["1"	"2 Оператор"	"3 Дата прихода сим"	"4 ЛК"	"5 Мобильный номер (MSISDN)"	"ICCID"	"Дата активации на Госуслугах"	"Тип Симкарты на Госуслугах"	"Тип модемов"	"Адрес установки"	"Получена"	"Активирована"	"Дата возврата симкарты"	"Тариф"	"Трафик"	Абон плата	Состояние симкарт	Контрагент	Устройство	Состояние ( Адрес)	Где симка физически	Комментарий	ДО какого блок	Устройство в котором была ранее	Дата отправки новому клиенту	Предыдущая стоимость	дата возврата	от кого вернулась симкарта	из какого устройства	"дата возврата"	"от кого вернулась симкарта"	"из какого устройства"	"дата возврата"	"от кого вернулась симкарта"	"из какого устройства"]
            data = self.worksheet.get_all_records()
            results = []
            
            for record in data:
                if name.lower() in str(record.get('Устройство', '')).lower():
                    results.append(record)
            return results
        except Exception as e:
            print(f"Ошибка при поиске по имени: {e}")
            return []

    def get_all_data(self) -> pd.DataFrame:
        """
        Получение всех данных из таблицы в виде DataFrame
        
        Returns:
            pd.DataFrame: DataFrame с данными из таблицы
        """
        try:
            data = self.worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
            return pd.DataFrame()

    def add_record(self, record: Dict) -> bool:
        """
        Добавление новой записи в таблицу
        
        Args:
            record (Dict): Словарь с данными для добавления
            
        Returns:
            bool: True если запись успешно добавлена, False в случае ошибки
        """
        try:
            self.worksheet.append_row(list(record.values()))
            return True
        except Exception as e:
            print(f"Ошибка при добавлении записи: {e}")
            return False

    def update_record(self, phone: str, new_data: Dict) -> bool:
        """
        Обновление существующей записи
        
        Args:
            phone (str): Номер телефона записи для обновления
            new_data (Dict): Новые данные для записи
            
        Returns:
            bool: True если запись успешно обновлена, False в случае ошибки
        """
        try:
            # Находим строку с указанным телефоном
            cell = self.worksheet.find(phone)
            if cell:
                # Обновляем данные в найденной строке
                row = cell.row
                for col, value in enumerate(new_data.values(), start=1):
                    self.worksheet.update_cell(row, col, value)
                return True
            return False
        except Exception as e:
            print(f"Ошибка при обновлении записи: {e}")
            return False

# Пример использования:
if __name__ == "__main__":
    # Создание экземпляра процессора
    processor = GoogleSheetsProcessor()
    
    # Пример поиска по телефону
    #result = processor.search_by_phone("+79001234567")
    #if result:
    #    print("Найдена запись:", result)
    
    # Пример поиска по имени
    results = processor.search_by_name("vkusvill-211")
    if results:
        print("Найдены записи:", results)
    
    # Пример получения всех данных
    #all_data = processor.get_all_data()
    #print("Все данные:", all_data) 