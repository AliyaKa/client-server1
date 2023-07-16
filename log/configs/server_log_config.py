from common.variables import LOGGING_LEVEL, ENCODING
import os
import logging.handlers
import logging
import sys

sys.path.append('../')

# создаём формировщик логов (formatter):
server_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(filename)s %(message)s')

# путь для логов
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = os.path.join(path, 'logs/server/server.log')

# создаём потоки вывода логов
steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(server_formatter)
steam.setLevel(logging.INFO)
log_file = logging.handlers.TimedRotatingFileHandler(
    path, encoding=ENCODING, interval=1, when='D')
log_file.setFormatter(server_formatter)

# создаём регистратор и настраиваем его
logger = logging.getLogger('server')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)

# отладка
if __name__ == '__main__':
    logger.critical('Test critical event')
    logger.error('Test error ivent')
    logger.debug('Test debug ivent')
    logger.info('Test info ivent')
