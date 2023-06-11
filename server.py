""" серверная часть """
import argparse
import json
import logging
import log.server_log_config
import socket
import sys
from common.variables import DEFAULT_PORT, PRESENCE, ACTION, TIME, \
    USER, ACCOUNT_NAME, MAX_CONNECTIONS, ERR_DICT, OK_DICT
from common.prgm_utils import get_message, send_message
from errors import IncorrectDataRecivedError, NonDictInputError

# Инициализация серверного логера
SERVER_LOGGER = logging.getLogger('server')


# формирует ответ на сообщение клиента
def parse_client_message(message):
    if ACTION in message \
            and message[ACTION] == PRESENCE \
            and TIME in message \
            and USER in message \
            and message[USER][ACCOUNT_NAME] == 'Guest':
        return OK_DICT
    return ERR_DICT


def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    return parser


def main():
    # определение порта
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if listen_port < 1024 or listen_port > 65535:
        SERVER_LOGGER.critical(f'Попытка запуска сервера с порта {listen_port}. '
                               f'Допустимы порты с 1024 до 65535.')
        sys.exit(1)
    SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {listen_port}, '
                       f'адрес: {listen_address}. '
                       f'Если адрес не указан, принимаются соединения с любых адресов.')

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((listen_address, listen_port))

    server.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = server.accept()
        SERVER_LOGGER.info(f'Установлено соедение с клиентом: {client_address}')
        try:
            message_from_client = get_message(client)  # получает сообщение от клиента
            SERVER_LOGGER.debug(f'Получено сервером сообщение от клиента: {message_from_client}')
            response = parse_client_message(message_from_client)  # формирует ответ клиенту
            SERVER_LOGGER.info(f'Ответ сервера клиенту: {response}')
            send_message(client, response)  # отправляет ответ клиенту
            SERVER_LOGGER.debug(f'Соединение с клиентом {client_address} завершено.')
            client.close()
            break
        except (ValueError, json.JSONDecodeError):
            SERVER_LOGGER.error(f'Некорректная JSON строка, полученная от '
                                f'клиента {client_address}. Соединение завершено.')
            client.close()
        except IncorrectDataRecivedError:
            SERVER_LOGGER.error(f'От клиента {client_address} приняты некорректные данные. '
                                f'Соединение завершено.')
            client.close()
        except NonDictInputError:
            SERVER_LOGGER.error(f'Сообщение от клиента {client_address} должен быть словарем. '
                                f'Соединение завершено.')
            client.close()


if __name__ == '__main__':
    main()
