import re
import PyPDF2
from logger import get_logger
from colorama import init, Fore, Style
from typing import List, Dict

init(autoreset=True)

logger = get_logger(__name__)


class PDFExtractor:
    def __init__(self):
        self.company_name_pattern = re.compile(
            r'(?:ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ|Полное наименование на русском языке)\s*"([^"]+)"',
            re.DOTALL | re.IGNORECASE
        )
        self.short_name_pattern = re.compile(
            r'Сокращенное наименование.*?(?:на русском языке)?\s*[:]{0,1}\s*((?:ООО|ОАО|ЗАО)\s*"[^"\n]+")',
            re.DOTALL | re.IGNORECASE
        )
        self.founder_pattern = re.compile(
            r'(?:Фамилия|Имя|Отчество)\s*(.*?)\s*(?:Фамилия|Имя|Отчество)\s*(.*?)\s*(?:Фамилия|Имя|Отчество)?\s*(.*?)\s*ИНН\s*(\d{10,12})',
            re.DOTALL
        )

    def extract_data(self, pdf_path):
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    page_text = page.extract_text()
                    page_text = self._preprocess_text(page_text)
                    text += page_text + '\n'

            data = {
                'full_name': self._extract_full_company_name(text),
                'short_name': self._extract_short_company_name(text),
                'founders': self._extract_founders(text),
                'full_text': text
            }

            logger.info(f"Successfully extracted data from {pdf_path}")
            return data
        except Exception as e:
            logger.error(f"Error extracting data from {pdf_path}: {str(e)}", exc_info=True)
            return None

    def _preprocess_text(self, text):
        text = re.sub(r'^\s*\d+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_full_company_name(self, text):
        match = self.company_name_pattern.search(text)
        if match:
            name = match.group(1).strip()
            logger.debug(f"Extracted full company name: {name}")
            return f'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "{name}"'
        logger.warning("Full company name not found in PDF")
        return ''

    def _extract_short_company_name(self, text):
        match = self.short_name_pattern.search(text)
        if match:
            name = match.group(1).strip()
            logger.debug(f"Extracted short company name: {name}")
            return name
        logger.warning("Short company name not found in PDF")
        return ''

    def _extract_founders(self, text) -> List[Dict[str, str]]:
        founders = set()
        matches = self.founder_pattern.finditer(text)
        for match in matches:
            full_name = ' '.join(filter(None, [match.group(1), match.group(2), match.group(3)]))
            full_name = ' '.join(full_name.split())
            inn = match.group(4).strip()
            founders.add((full_name, inn))

        if not founders:
            logger.warning("No founders found in PDF")

        return [{"name": name, "inn": inn} for name, inn in founders]


def print_formatted_data(data):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Extracted Data:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Full Company Name: {Style.RESET_ALL}{data['full_name']}")
    print(f"{Fore.GREEN}Short Company Name: {Style.RESET_ALL}{data['short_name']}")
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}Current Founders:{Style.RESET_ALL}")
    for i, founder in enumerate(data['founders'], 1):
        print(f"  {i}. {Fore.MAGENTA}Name: {Style.RESET_ALL}{founder['name']}")
        print(f"     {Fore.MAGENTA}INN: {Style.RESET_ALL}{founder['inn']}")



if __name__ == "__main__":
    extractor = PDFExtractor()
    pdf_path = "/Users/roma/work/ParcerINN/downloads/7704256957.pdf"
    data = extractor.extract_data(pdf_path)
    if data:
        print_formatted_data(data)
    else:
        print(f"{Fore.RED}Failed to extract data from PDF{Style.RESET_ALL}")