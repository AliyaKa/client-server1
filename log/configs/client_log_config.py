"""Конфиг клиентского логгера"""

import sys
import os
import logging

from common.variables import ENCODING, LOGGING_LEVEL, FORMATTER

sys.path.append('../')

# Подготовка имени файла для логирования
PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PATH = os.path.join(PATH, 'logs/client/client.log')

# создаём потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)
LOG_FILE = logging.FileHandler(PATH, encoding=ENCODING)
LOG_FILE.setFormatter(FORMATTER)

# создаём регистратор и настраиваем его
LOGGER = logging.getLogger('client')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOGGING_LEVEL)

# отладка
if __name__ == '__main__':
    LOGGER.critical('Критическая ошибка')
    LOGGER.error('Ошибка')
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
    logging.warning("Предупреждение")
