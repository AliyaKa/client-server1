"""клиентская часть"""
import argparse
import json
import logging
import threading

from decos import log
import socket
import sys
import time
from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from common.variables import DEFAULT_PORT, DEFAULT_IP, ACTION, TIME, USER, ACCOUNT_NAME, \
    PRESENCE, RESPONSE, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT, LOGGER
from common.prgm_utils import get_message, send_message
from metaclasses import ClientMaker


# Класс создания и отправки сообщений на сервер и взаимодействия с пользователем:
class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_exit_message(self):
        # Функция на создание словаря с сообщением о выходе
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        to = input('Кому:')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            LOGGER.info(f'Отправлено сообщение пользователю {to}')
        except:
            LOGGER.critical(f'Соединение с сервером прервано!')
            sys.exit(1)

    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду:')
            if command == 'msg':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.create_exit_message())
                except:
                    pass
                print('Завершение соединения.')
                LOGGER.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print(f'Команда {command} не распознана.')
                self.print_help()

    def print_help(self):
        # Список команд
        print('Поддерживаемые команды:')
        print('msg - отправить сообщение')
        print('help - вывести справку')
        print('exit - выход из программы')


# Класс приемник сообщений с сервера. Принимает сообщения, выводит в консоль.
class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message \
                        and message[ACTION] == MESSAGE \
                        and SENDER in message \
                        and DESTINATION in message \
                        and MESSAGE_TEXT in message \
                        and message[DESTINATION] == self.account_name:
                    print(f'Получено сообщение от пользователя '
                          f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    LOGGER.info(f'Получено сообщение от пользователя '
                                f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                else:
                    LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                LOGGER.critical(f'Соединение с сервером прервано!')
                break


@log
def create_presence_msg(account_name):
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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if server_port < 1024 or server_port > 65535:
        LOGGER.critical(
            f' Попытка запуска клиента с зарезервированным номером порта: {server_port}.'
            f' Допустимы порты с 1024 до 65535.')
        sys.exit(1)

    return server_address, server_port, client_name


@log
def main():
    # сообщение о запуске
    print('Консольный менеджер. Клиентксий модуль.')

    # загружаем параметры командной строки
    server_address, server_port, client_name = create_arg_parser()
    print(f'Имя пользователя: {client_name}')

    # если имя пользователя не задано, запросим пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_name}')
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence_msg(client_name))
        answer = answer_server(get_message(transport))
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
        # запускаем клиентский процесс приема сообщений.
        receiver = ClientReader(client_name, transport)
        receiver.daemon = True
        receiver.start()

        # запускаем отправку сообщений и взаимодействие с пользователем.
        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        LOGGER.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
