from google_sheets_handler import \
    GoogleSheetsHandler  # Предполагается, что класс GoogleSheetsHandler находится в файле google_sheets_handler.py


def main():
    # Создаем инстанс класса GoogleSheetsHandler
    handler = GoogleSheetsHandler()

    # Вызываем метод для очистки столбцов C, D, и E
    handler.clear_columns_cde()


if __name__ == "__main__":
    main()