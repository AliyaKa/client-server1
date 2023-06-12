"""клиентская часть"""
import argparse
import json
from decos import log
import socket
import sys
import time
from errors import ReqFieldMissingError
from common.variables import DEFAULT_PORT, DEFAULT_IP, ACTION, TIME, USER, ACCOUNT_NAME, \
    PRESENCE, RESPONSE, ERROR, LOGGER
from common.prgm_utils import get_message, send_message


@log
def create_presence_msg(account_name='Guest'):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
    return out


@log
def answer_server(message):
    if RESPONSE in message:
        LOGGER.debug(f'Разбор ответа сервера: {message}')
        if message[RESPONSE] == 200:
            LOGGER.debug(f'Успешный ответ : {message[RESPONSE]}: OK')
            return '200 : OK'
        LOGGER.error(f'Ответ сервера 400 : {message[ERROR]}. Отсутствует обязательное поле')
        return f'400 : {message[ERROR]}'
    raise ReqFieldMissingError(RESPONSE)


@log
def create_arg_parser():
    # Функция для создания парсера аргументов командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    return parser


@log
def main():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port

    try:
        if server_port < 1024 or server_port > 65535:
            LOGGER.critical(
                f' Попытка запуска клиента с зарезервированным номером порта: {server_port}.'
                f' Допустимы порты с 1024 до 65535.')
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP
        server_port = DEFAULT_PORT
        LOGGER.info(f'Параметры клиента выбраны по умолчанию.')
    except ValueError:
        print(
            'Порт - это число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_address, server_port))

    message_to_server = create_presence_msg()
    send_message(client, message_to_server)

    #  Получаем ответ
    try:
        answer = answer_server(get_message(client))
        LOGGER.info(f'Принят ответ от сервера {answer}')
        print(answer)
    except (ValueError, json.JSONDecodeError):
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        print('Не удалось декодировать сообщение сервера.')
    except ConnectionRefusedError:
        LOGGER.critical(
            f'Не удалось подключиться к серверу {server_address} : {server_port}, '
            f'удаленный компьютер отклонил запрос на подключение.')


if __name__ == '__main__':
    main()
