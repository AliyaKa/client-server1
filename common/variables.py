"""константы"""
import logging

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

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'


ERR_DICT = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

OK_DICT = {RESPONSE: 200}

# Текущий уровень логирования
LOGGING_LEVEL = logging.DEBUG
# создаём формировщик логов (formatter):
FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
