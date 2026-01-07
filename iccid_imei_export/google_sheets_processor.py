import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pandas as pd
from typing import List, Dict, Optional, Union
from tabulate import tabulate

class GoogleSheetsProcessor:
    def __init__(self, credentials_file: str = 'client_secret.json', token_file: str = None):
        """
        Инициализация процессора Google таблиц с использованием OAuth 2.0
        
        Args:
            credentials_file (str): Путь к файлу с учетными данными OAuth 2.0
            token_file (str): Путь к файлу с токеном. Если None, используется token.json в той же директории, что и credentials_file
        """
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        self.credentials_file = credentials_file
        
        # Определяем путь к token.json
        if token_file:
            self.token_file = token_file
        else:
            # Используем token.json в той же директории, что и credentials_file
            creds_dir = os.path.dirname(os.path.abspath(credentials_file))
            self.token_file = os.path.join(creds_dir, 'token.json')
        
        self.creds = None
        self.spreadsheet_id = '1nx2QSynzcvt_gOb8gsC0l6Zs7nb7V_x-19kOLx93-WI'
        
        # Проверяем наличие сохраненных учетных данных
        if os.path.exists(self.token_file):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            except Exception as e:
                # Если не удалось загрузить токен (например, несовместимые scope), удаляем старый и создаем новый
                print(f"[ПРЕДУПРЕЖДЕНИЕ] Не удалось загрузить существующий токен: {e}")
                print("[ИНФО] Удаляем старый токен и создадим новый")
                try:
                    os.remove(self.token_file)
                except:
                    pass
                self.creds = None
        
        # Если нет действительных учетных данных, запрашиваем новые
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    # Если не удалось обновить токен (например, несовместимые scope), удаляем старый и создаем новый
                    print(f"[ПРЕДУПРЕЖДЕНИЕ] Не удалось обновить токен: {e}")
                    print("[ИНФО] Удаляем старый токен и создадим новый")
                    try:
                        os.remove(self.token_file)
                    except:
                        pass
                    self.creds = None
            
            # Если токен все еще недействителен, создаем новый
            if not self.creds or not self.creds.valid:
                # Используем абсолютный путь к credentials_file
                abs_credentials_file = os.path.abspath(self.credentials_file)
                flow = InstalledAppFlow.from_client_secrets_file(
                    abs_credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Сохраняем учетные данные для следующего запуска
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
        self.worksheet = self.spreadsheet.worksheet('SIMS')  # Замените на нужный лист
