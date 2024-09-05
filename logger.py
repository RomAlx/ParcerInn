import logging
import os
from logging.handlers import RotatingFileHandler
from config import LOG_FILE, LOG_LEVEL, BASE_DIR


def setup_logger(name='ParserINN'):
    """
    Настраивает и возвращает логгер с заданными параметрами.

    :param name: Имя логгера
    :return: Настроенный объект логгера
    """
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Создаем форматтер
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Обработчик для записи в файл
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Создаем и настраиваем корневой логгер
root_logger = setup_logger()


def get_logger(name):
    """
    Возвращает настроенный логгер для заданного имени.

    :param name: Имя модуля или компонента
    :return: Настроенный объект логгера
    """
    return logging.getLogger(name)


# Функция для логирования необработанных исключений
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """
    Логирует необработанные исключения.
    """
    root_logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


# Устанавливаем обработчик необработанных исключений
import sys

sys.excepthook = log_uncaught_exceptions