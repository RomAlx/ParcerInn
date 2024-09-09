import re
import os
import pdfplumber
from typing import List, Dict
from datetime import datetime
import time


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
            r'(?:Фамилия\s+(.*?)\s*Имя\s+(.*?)\s*Отчество\s+(.*?)\s*|Фамилия\s+(.*?)\s*Имя\s+(.*?)\s*)ИНН\s*(\d{10,12}).*?Номинальная стоимость доли \(в рублях\)\s*(\d+).*?Размер доли \(в процентах\)\s*(\d+(?:\.\d+)?)',
            re.DOTALL
        )
        self.grn_date_pattern = re.compile(
            r'ГРН и дата внесения в ЕГРЮЛ(?: записи| сведений)[^,\d]*(\d{13})[^0-9]+(\d{2}\.\d{2}\.\d{4})',
            re.DOTALL
        )

    def extract_data(self, pdf_path: str) -> Dict[str, any]:
        start_time = time.time()
        print(f"Starting extraction from {pdf_path}")

        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                print(f"PDF opened. Number of pages: {len(pdf.pages)}")
                text = self._extract_text(pdf)

            if not text.strip():
                print("Extracted text is empty. Cannot proceed with data extraction.")
                return None

            print("Text extracted successfully. Proceeding with data extraction...")

            founders_section = self._get_founders_section(text)
            print(f"Founders section length: {len(founders_section)}")
            print("First 500 characters of founders section:")
            print(founders_section[:500])

            founders = self._extract_founders(founders_section)

            data = {
                'full_name': self._extract_full_company_name(text),
                'short_name': self._extract_short_company_name(text),
                'founders': founders,
                'latest_date': self._get_latest_grn_from_founders(founders),
            }

            end_time = time.time()
            print(f"Extraction completed in {end_time - start_time:.2f} seconds")
            return data
        except Exception as e:
            print(f"Error extracting data from {pdf_path}: {str(e)}")
            return None

    def _extract_text(self, pdf) -> str:
        text = ""
        for i, page in enumerate(pdf.pages):
            try:
                page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
                text += self._preprocess_text(page_text) + '\n'
                if i % 10 == 0:
                    print(f"Processed {i + 1} pages...")
            except Exception as e:
                print(f"Warning: Error extracting text from page {i + 1}: {str(e)}")
        return text

    def _preprocess_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _get_founders_section(self, text: str) -> str:
        founders_section = re.search(
            r'Сведения об участниках / учредителях юридического лица(.*?)Сведения о видах экономической деятельности',
            text, re.DOTALL)
        if founders_section:
            return founders_section.group(1)
        return ""

    def _extract_full_company_name(self, text: str) -> str:
        print("Extracting full company name...")
        match = self.company_name_pattern.search(text)
        if match:
            name = match.group(1).strip()
            print(f"Full company name found: {name}")
            return f'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "{name}"'
        print("Full company name not found")
        return ''

    def _extract_short_company_name(self, text: str) -> str:
        print("Extracting short company name...")
        match = self.short_name_pattern.search(text)
        if match:
            name = match.group(1).strip()
            print(f"Short company name found: {name}")
            return name
        print("Short company name not found")
        return ''

    def _extract_founders(self, text: str) -> List[Dict[str, str]]:
        print("Extracting founders...")
        founders = []
        start_time = time.time()

        matches = list(self.founder_pattern.finditer(text))
        print(f"Found {len(matches)} potential founders")

        for i, match in enumerate(matches):
            if match.group(1):  # Если есть отчество
                full_name = f"{match.group(1)} {match.group(2)} {match.group(3)}".strip()
                inn = match.group(6)
                nominal_value = match.group(7)
                share_percentage = match.group(8)
            else:  # Если отчества нет
                full_name = f"{match.group(4)} {match.group(5)}".strip()
                inn = match.group(6)
                nominal_value = match.group(7)
                share_percentage = match.group(8)

            # Извлекаем ГРН и дату для текущего учредителя
            founder_info = text[max(0, match.start() - 500):match.start()]
            print(f"\nFounder {i + 1} info (500 chars before):")
            print(founder_info)

            grn_date = self._get_latest_grn_date(founder_info)

            founders.append({
                "name": full_name.split()[0:3],  # Убираем лишние цифры из имени
                "inn": inn,
                "nominal_value": nominal_value,
                "share_percentage": share_percentage,
                "latest_grn": grn_date['grn'],
                "latest_date": grn_date['date']
            })
            print(f"Processed founder {i + 1}: {' '.join(founders[-1]['name'])}")
            print(f"  GRN: {grn_date['grn']}, Date: {grn_date['date']}")

        print(f"Extracted {len(founders)} founders in {time.time() - start_time:.2f} seconds")
        return founders

    def _get_latest_grn_date(self, text: str) -> Dict[str, str]:
        matches = list(self.grn_date_pattern.finditer(text))

        if matches:
            # Берем последнее совпадение, так как оно, вероятно, самое актуальное
            latest_entry = matches[-1]
            grn = latest_entry.group(1)
            date = latest_entry.group(2)
            return {"grn": grn, "date": date}

        print("No GRN and date found in the following text:")
        print(text)
        return {"grn": "", "date": ""}

    def _get_latest_grn_from_founders(self, founders: List[Dict[str, str]]) -> str:
        if not founders:
            ""

        # Найдем самую свежую дату
        latest = max(founders, key=lambda x: datetime.strptime(x['latest_date'], '%d.%m.%Y'))
        print(f"Latest GRN from founders: GRN: {latest['latest_grn']}, Date: {latest['latest_date']}")
        return latest['latest_date']


# Пример использования
if __name__ == "__main__":
    extractor = PDFExtractor()
    pdf_path = "/Users/roma/work/ParcerINN/downloads/7704256957.pdf"
    print(f"Starting extraction from {pdf_path}")
    data = extractor.extract_data(pdf_path)
    if data:
        print("\nExtracted Data:")
        print("Full Company Name:", data['full_name'])
        print("Short Company Name:", data['short_name'])
        print("Latest GRN Info:")
        print(f"Date: {data['latest_date']}")
        print("Founders:")
        for founder in data['founders']:
            print(f"  Name: {' '.join(founder['name'])}")
            print(f"  INN: {founder['inn']}")
            print(f"  Nominal Value: {founder['nominal_value']}")
            print(f"  Share Percentage: {founder['share_percentage']}")
            print(f"  Latest GRN: {founder['latest_grn']}")
            print(f"  Latest Date: {founder['latest_date']}")
    else:
        print("Failed to extract data from PDF")