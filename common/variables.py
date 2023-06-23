"""константы"""
import logging
import sys

# Порт поумолчанию для сетевого ваимодействия
DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длина сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'

SENDER = 'from'
DESTINATION = 'to'


# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'

EXIT = 'exit'

ERR_DICT = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

OK_DICT = {RESPONSE: 200}

# Текущий уровень логирования
LOGGING_LEVEL = logging.DEBUG
# создаём формировщик логов (formatter):
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s (%(filename)s) %(message)s')

# метод определения модуля, источника запуска.
# Метод find () возвращает индекс первого вхождения искомой подстроки,
# если он найден в данной строке.
# Если его не найдено, - возвращает -1.

if sys.argv[0].find('client.py') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


