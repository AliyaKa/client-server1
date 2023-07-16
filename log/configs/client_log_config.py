"""Конфиг клиентского логгера"""

import sys
import os
import logging

from common.variables import ENCODING, LOGGING_LEVEL

client_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(filename)s %(message)s')
sys.path.append('../')

# Подготовка имени файла для логирования
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = os.path.join(path, 'logs/client/client.log')

# создаём потоки вывода логов
steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(client_formatter)
steam.setLevel(logging.INFO)
log_file = logging.FileHandler(path, encoding=ENCODING)
log_file.setFormatter(client_formatter)

# создаём регистратор и настраиваем его
logger = logging.getLogger('client')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)

# отладка
if __name__ == '__main__':
    logger.critical('Test critical event')
    logger.error('Test error ivent')
    logger.debug('Test debug ivent')
    logger.info('Test info ivent')
