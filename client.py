"""клиентская часть"""
import argparse
import json
from decos import log
import socket
import sys
import time
from errors import ReqFieldMissingError, ServerError
from common.variables import DEFAULT_PORT, DEFAULT_IP, ACTION, TIME, USER, ACCOUNT_NAME, \
    PRESENCE, RESPONSE, ERROR, LOGGER, MESSAGE, MESSAGE_TEXT, SENDER
from common.prgm_utils import get_message, send_message


@log
def message_from_server(message):
    if ACTION in message \
            and message[ACTION] == MESSAGE \
            and SENDER in message \
            and MESSAGE_TEXT in message:
        print(f'Получено сообщение от пользователя '
              f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        LOGGER.info(f'Получено сообщение от пользователя '
                    f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
    else:
        LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')


@log
def create_message(sock, account_name='Guest'):
    message = input('Введите сообщение для отправки или \'!!!\' для завершения работы: ')
    if message == '!!!':
        sock.close()
        LOGGER.info('Завершение работы по команде пользователя.')
        print('Спасибо за использование нашего сервиса!')
        sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: message
    }
    LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
    return message_dict


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
        elif message[RESPONSE] == 400:
            LOGGER.error(f'Ответ сервера 400 : {message[ERROR]}. Отсутствует обязательное поле')
        raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def create_arg_parser():
    # Функция для создания парсера аргументов командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode
    if server_port < 1024 or server_port > 65535:
        LOGGER.critical(
            f' Попытка запуска клиента с зарезервированным номером порта: {server_port}.'
            f' Допустимы порты с 1024 до 65535.')
        sys.exit(1)

    if client_mode not in ('listen', 'send'):
        LOGGER.critical(f'Указан недопустимый режим работы {client_mode}, '
                        f'допустимые режимы: listen , send')
        sys.exit(1)
    return server_address, server_port, client_mode


@log
def main():
    server_address, server_port, client_mode = create_arg_parser()
    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_mode}')
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_address, server_port))
        send_message(client, create_presence_msg())
        answer = answer_server(get_message(client))
        LOGGER.info(f'Принят ответ от сервера {answer}')
        print(f'Установлено соединение с сервером')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except ServerError as error:
        LOGGER.error(f'При установке соединения сервер вернул ошибку {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        LOGGER.critical(
            f'Не удалось подключиться к серверу {server_address} : {server_port}, '
            f'удаленный компьютер отклонил запрос на подключение.')
    else:
        # Если соединение с сервером установлено корректно,
        # начинаем обмен с ним, согласно требуемому режиму.
        # основной цикл прогрммы:
        if client_mode == 'send':
            print('Режим работы - отправка сообщений.')
        else:
            print('Режим работы - приём сообщений.')
        while True:
            # режим работы - отправка сообщений
            if client_mode == 'send':
                try:
                    send_message(client, create_message(client))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)

            # Режим работы приём:
            if client_mode == 'listen':
                try:
                    message_from_server(get_message(client))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {server_address} было потеряно.')
                    sys.exit(1)


if __name__ == '__main__':
    main()
