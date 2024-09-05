import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Базовые настройки проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Настройки Google Sheets
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

# Настройки парсера EGRUL
EGRUL_URL = 'https://egrul.nalog.ru/index.html'
PDF_DOWNLOAD_PATH = os.path.join(BASE_DIR, 'downloads')

# Настройки обработки данных
MAX_RETRIES = 3
RETRY_DELAY = 5  # в секундах

# Настройки логирования
LOG_FILE = os.path.join(BASE_DIR, 'parcer_inn.log')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Настройки планировщика
UPDATE_TIME = os.getenv('UPDATE_TIME', "00:00")  # Время ежедневного обновления

# Настройки колонок в Google Sheets
COLUMN_INN = 'A'
COLUMN_NAME = 'B'
COLUMN_CURRENT_FOUNDERS = 'C'
COLUMN_FORMER_FOUNDERS = 'D'
COLUMN_CHANGE_DATE = 'E'

# Прочие настройки
TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))  # Тайм-аут для запросов в секундах
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Настройки прокси (если требуется)
PROXY = os.getenv('PROXY_URL')

# Функция для получения абсолютного пути к файлу в директории проекта
def get_project_path(relative_path):
    return os.path.abspath(os.path.join(BASE_DIR, relative_path))

# Проверка наличия критически важных настроек
if not SHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID не установлен. Пожалуйста, добавьте его в файл .env")

if not os.path.exists(CREDENTIALS_FILE):
    raise FileNotFoundError(f"Файл credentials.json не найден по пути {CREDENTIALS_FILE}")

# Создание директории для загрузки PDF, если она не существует
if not os.path.exists(PDF_DOWNLOAD_PATH):
    os.makedirs(PDF_DOWNLOAD_PATH)