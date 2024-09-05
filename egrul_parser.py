import os
import time
import logging
import glob
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from config import EGRUL_URL, MAX_RETRIES, RETRY_DELAY, TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()


class EgrulParser:
    def __init__(self):
        options = Options()
        options.add_argument(f'user-agent={USER_AGENT}')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')

        self.project_path = os.getenv('PROJECT_PATH')
        if not self.project_path:
            raise ValueError("PROJECT_PATH должен быть указан в файле .env")

        self.download_path = os.path.join(self.project_path, 'downloads')
        os.makedirs(self.download_path, exist_ok=True)

        prefs = {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def wait_for_element(self, by, value, timeout=TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def get_pdf(self, inn):
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Попытка {attempt + 1} получить данные для ИНН: {inn}")
                self.driver.get(EGRUL_URL)

                inn_input = self.wait_for_element(By.NAME, "query")
                inn_input.clear()
                inn_input.send_keys(inn)
                logger.info(f"Введен ИНН: {inn}")

                search_button = self.wait_for_element(By.ID, "btnSearch")
                search_button.click()
                logger.info("Нажата кнопка поиска")

                time.sleep(5)

                self.check_search_results(inn)

                excerpt_button = self.find_excerpt_button()
                if excerpt_button:
                    self.click_button_with_js(excerpt_button)
                    logger.info("Нажата кнопка 'Получить выписку'")
                else:
                    logger.error("Не найдена кнопка 'Получить выписку'")
                    self.save_screenshot(f"error_screenshot_{inn}_no_button.png")
                    continue

                time.sleep(10)

                pdf_path = self.find_and_rename_pdf(inn)
                if pdf_path:
                    logger.info(f"PDF успешно скачан и переименован: {pdf_path}")
                    return pdf_path
                else:
                    logger.error(f"Не удалось найти или переименовать PDF файл для ИНН: {inn}")

            except TimeoutException as e:
                logger.warning(f"Таймаут при ожидании элемента для ИНН: {inn}. Ошибка: {str(e)}")
                self.save_screenshot(f"timeout_screenshot_{inn}.png")
            except Exception as e:
                logger.error(f"Ошибка при попытке получить данные для ИНН: {inn}. Ошибка: {str(e)}", exc_info=True)
                self.save_screenshot(f"error_screenshot_{inn}.png")

            time.sleep(RETRY_DELAY)

        logger.error(f"Не удалось получить PDF для ИНН: {inn} после {MAX_RETRIES} попыток")
        return None

    def check_search_results(self, inn):
        logger.info("Проверка результатов поиска")

        if self.check_element_exists(By.ID, "pnl-result"):
            logger.info("Найдена панель результатов")
            result_rows = self.driver.find_elements(By.CSS_SELECTOR, ".res-text")
            for row in result_rows:
                if inn in row.text:
                    logger.info(f"Найден результат для ИНН: {inn}")
                    return
            logger.warning(f"Результат для ИНН {inn} не найден в списке")
        elif self.check_element_exists(By.ID, "pnl-nodata"):
            logger.warning(f"Нет данных для ИНН: {inn}")
        else:
            logger.warning("Не найдены ни результаты, ни сообщение об отсутствии данных")
        logger.info(f"Текущий URL: {self.driver.current_url}")
        logger.info(f"Исходный код страницы: {self.driver.page_source[:500]}...")

    def check_element_exists(self, by, value):
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def find_excerpt_button(self):
        try:
            return WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-excerpt') and contains(text(), 'Получить выписку')]"))
            )
        except TimeoutException:
            logger.warning("Кнопка 'Получить выписку' не найдена или не кликабельна")
            return None

    def click_button_with_js(self, button):
        self.driver.execute_script("arguments[0].click();", button)

    def find_and_rename_pdf(self, inn):
        # Ищем файл, начинающийся с 'ul' и заканчивающийся на '.pdf'
        pdf_files = glob.glob(os.path.join(self.download_path, 'ul-*.pdf'))
        if pdf_files:
            # Берем самый свежий файл, если их несколько
            latest_pdf = max(pdf_files, key=os.path.getctime)
            new_filename = f"{inn}.pdf"
            new_filepath = os.path.join(self.download_path, new_filename)
            os.rename(latest_pdf, new_filepath)
            return new_filepath
        return None

    def __del__(self):
        self.driver.quit()


if __name__ == "__main__":
    parser = EgrulParser()
    inn = "7704256957"
    pdf_path = parser.get_pdf(inn)
    if pdf_path:
        print(f"PDF файл был успешно скачан и переименован: {pdf_path}")
    else:
        print("Не удалось получить PDF файл.")