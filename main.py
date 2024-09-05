import time
import schedule
from datetime import datetime
import logging
from google_sheets_handler import GoogleSheetsHandler
from egrul_parser import EgrulParser
from pdf_extractor import PDFExtractor
from data_processor import DataProcessor
from logger import setup_logger

logger = setup_logger()


def process_companies():
    try:
        logger.info("Starting data processing")
        gs_handler = GoogleSheetsHandler()
        egrul_parser = EgrulParser()
        pdf_extractor = PDFExtractor()
        data_processor = DataProcessor()

        inn_list = gs_handler.get_inn_list()

        for inn in inn_list:
            try:
                logger.info(f"Processing INN: {inn}")
                pdf_file = egrul_parser.get_pdf(inn)
                if not pdf_file:
                    logger.warning(f"Failed to get PDF for INN: {inn}")
                    continue

                pdf_data = pdf_extractor.extract_data(pdf_file)
                logger.info(f"Extracted data from PDF for INN {inn}: {pdf_data}")
                logger.info(f"Number of founders extracted: {len(pdf_data.get('founders', []))}")

                current_data = gs_handler.get_company_data(inn)
                logger.info(f"Current data for INN {inn}: {current_data}")

                processed_data = data_processor.process(inn, pdf_data, current_data)
                logger.info(f"Processed data for INN {inn}: {processed_data}")
                logger.info(
                    f"Number of current founders after processing: {len(processed_data['current_founders'].split(','))}")
                logger.info(
                    f"Number of former founders after processing: {len(processed_data['former_founders'].split(','))}")

                update_result = gs_handler.update_company_data(inn, processed_data)
                logger.info(f"Update result for INN {inn}: {update_result}")

            except Exception as e:
                logger.error(f"Error processing INN {inn}: {str(e)}", exc_info=True)

        logger.info("Data processing completed")
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}", exc_info=True)


def run_scheduler():
    logger.info("Scheduler started")
    schedule.every(24).hours.do(process_companies)

    # Запускаем процесс сразу при старте
    process_companies()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
