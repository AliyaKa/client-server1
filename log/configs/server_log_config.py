import logging
import logging.handlers
import os
import sys

from common.variables import ENCODING, FORMATTER, LOGGING_LEVEL

sys.path.append('../')

# путь для логов
PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PATH = os.path.join(PATH, 'logs/server/server.log')

# создаём потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)

# ежедневная ротация лог-файлов
LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding=ENCODING, interval=1, when='M')
LOG_FILE.setFormatter(FORMATTER)

# создаём регистратор и настраиваем его
LOGGER = logging.getLogger('server')
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



