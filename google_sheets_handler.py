import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import SHEET_ID, CREDENTIALS_FILE, COLUMN_INN, COLUMN_NAME, COLUMN_CURRENT_FOUNDERS, COLUMN_FORMER_FOUNDERS, \
    COLUMN_CHANGE_DATE

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoogleSheetsHandler:
    def __init__(self):
        self.sheet_id = SHEET_ID
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Аутентификация в Google Sheets API."""
        try:
            self.creds = Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=self.creds)
            logger.info("Successfully authenticated with Google Sheets API")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            raise

    def get_inn_list(self):
        """Получает список ИНН из таблицы."""
        try:
            range_name = f'{COLUMN_INN}2:{COLUMN_INN}'
            logger.info(f"Fetching INN list from range: {range_name}")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id, range=range_name).execute()
            values = result.get('values', [])
            inn_list = [row[0] for row in values if row]
            logger.info(f"Retrieved {len(inn_list)} INN numbers")
            return inn_list
        except HttpError as error:
            logger.error(f"Error fetching INN list: {error}")
            return []

    def get_company_data(self, inn):
        try:
            range_name = f'{COLUMN_INN}2:{COLUMN_CHANGE_DATE}'
            logger.info(f"Fetching company data for INN {inn}")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id, range=range_name).execute()
            values = result.get('values', [])
            for row in values:
                if row[0] == inn:
                    company_data = {
                        'inn': row[0],
                        'name': row[1] if len(row) > 1 else '',  # Короткое название
                        'current_founders': row[2] if len(row) > 2 else '',
                        'former_founders': row[3] if len(row) > 3 else '',
                        'change_date': row[4] if len(row) > 4 else ''
                    }
                    logger.info(f"Found data for INN {inn}: {company_data}")
                    return company_data
            logger.warning(f"Company with INN {inn} not found in the sheet")
            return None
        except HttpError as error:
            logger.error(f"Error fetching company data for INN {inn}: {error}")
            return None

    def update_company_data(self, inn, data):
        try:
            range_name = f'{COLUMN_INN}2:{COLUMN_INN}'
            logger.info(f"Searching for INN {inn} to update data")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id, range=range_name).execute()
            values = result.get('values', [])
            row_index = None
            for i, row in enumerate(values, start=2):
                if row and row[0] == inn:
                    row_index = i
                    break

            if row_index is None:
                logger.warning(f"Company with INN {inn} not found for update")
                return False

            range_name = f'{COLUMN_INN}{row_index}:{COLUMN_CHANGE_DATE}{row_index}'
            values = [
                [
                    inn,
                    data.get('name', ''),
                    data.get('current_founders', ''),
                    data.get('former_founders', ''),
                    data.get('change_date', '')
                ]
            ]
            body = {'values': values}
            logger.info(f"Updating data for INN {inn}: {values}")
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id, range=range_name,
                valueInputOption='USER_ENTERED', body=body).execute()
            logger.info(f"Successfully updated data for INN {inn}")
            return True
        except HttpError as error:
            logger.error(f"Error updating company data for INN {inn}: {error}")
            return False

    def clear_columns_cde(self):
        """Очищает содержимое столбцов C, D и E начиная со второй строки."""
        try:
            # Определяем диапазон столбцов C, D и E начиная со второй строки
            range_name = f'C2:E'
            logger.info(f"Clearing content in range {range_name}")

            # Создаем пустой диапазон данных для удаления
            result = self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id, range=range_name).execute()
            num_rows = len(result.get('values', []))  # Считаем количество строк

            # Создаем пустые значения для каждой строки в диапазоне C2:E
            values = [['' for _ in range(3)] for _ in range(num_rows)]

            body = {'values': values}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id, range=range_name,
                valueInputOption='USER_ENTERED', body=body).execute()

            logger.info(f"Successfully cleared content in columns C, D, E")
        except HttpError as error:
            logger.error(f"Error clearing columns C, D, and E: {error}")


def test_google_sheets_handler():
    handler = GoogleSheetsHandler()

    print("Testing get_inn_list:")
    inn_list = handler.get_inn_list()
    print(f"Retrieved {len(inn_list)} INN numbers. First 5: {inn_list[:5]}")

    if inn_list:
        test_inn = inn_list[0]
        print(f"\nTesting get_company_data for INN {test_inn}:")
        company_data = handler.get_company_data(test_inn)
        print(f"Company data: {company_data}")

        print(f"\nTesting update_company_data for INN {test_inn}:")
        update_data = {
            'name': 'Test Company Name',
            'current_founders': 'Test Current Founder',
            'former_founders': 'Test Former Founder',
            'change_date': '2023-09-01'
        }
        update_result = handler.update_company_data(test_inn, update_data)
        print(f"Update result: {update_result}")

        print(f"\nVerifying update for INN {test_inn}:")
        updated_data = handler.get_company_data(test_inn)
        print(f"Updated company data: {updated_data}")
    else:
        print("No INN numbers found for testing.")


if __name__ == "__main__":
    test_google_sheets_handler()