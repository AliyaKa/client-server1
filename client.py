"""клиентская часть"""
import argparse
import json
import logging
import threading

from PyQt5.QtWidgets import QApplication

from client_database import ClientDB
from decos import log
import socket
import sys
import time

from errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
from common.variables import DEFAULT_PORT, DEFAULT_IP, ACTION, TIME, USER, ACCOUNT_NAME, \
    PRESENCE, RESPONSE, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT, LOGGER, GET_CONTACTS, LIST_INFO, \
    ADD_CONTACT, USERS_REQUEST, REMOVE_CONTACT
from common.prgm_utils import get_message, send_message
from metaclasses import ClientMaker

# Объект блокировки сокета и работы с БД
sock_lock = threading.Lock()
database_lock = threading.Lock()


# Класс создания и отправки сообщений на сервер и взаимодействия с пользователем:
class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        # Функция на создание словаря с сообщением о выходе
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    # Функция запрашивает кому отправить сообщение, само сообщение, и отправляет полученные данные на сервер
    def create_message(self):
        to = input('Кому:')
        message = input('Введите сообщение для отправки: ')

        # проверка, что получатель есть в БД
        with database_lock:
            if not self.database.check_user(to):
                LOGGER.error(f'Попытка отправить сообщение не зарегестрированному получателю {to}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Сохраним сообщение для истории
        with database_lock:
            self.database.save_message(self.account_name, to, message)

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                LOGGER.info(f'Отправлено сообщение пользователю {to}')
            except OSError as err:
                if err.errno:
                    LOGGER.critical(f'Соединение с сервером прервано!')
                    sys.exit(1)
                else:
                    LOGGER.error('Не удалось передать сообщение. Таймаут соединения')

    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
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
            elif command == 'contacts':
                with database_lock:
                    contact_list = self.database.get_contacts()
                for contact in contact_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print(f'Команда {command} не распознана.')
                self.print_help()

    def print_help(self):
        # Список команд
        print('Поддерживаемые команды:')
        print('msg - отправить сообщение')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести справку')
        print('exit - выход из программы')

    def print_history(self):
        ask = input('Входящие сообщения введите in, исходящие - out, все сообщения - клавиша Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'Сообщение от пользователя: {message[0]} от {message[3]}: \n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'Сообщение пользователю: {message[1]} от {message[3]}: \n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, '
                          f'пользователю {message[1]} от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Введите del - чтобы удалить, add - чтобы добавить ')
        if ans == 'del':
            edit = input('Введите имя контакта, который необходимо удалить: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    LOGGER.error('Данного контакта не существует.')
        elif ans == 'add':
            edit = input('Введите имя контакта, который необходимо добавить: ')
            # Проверка на существование контакта
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        self.database.add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        LOGGER.error('Не удалось отправить информацию на сервер.')


# Класс приемник сообщений с сервера. Принимает сообщения, выводит в консоль.
class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()


    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                # Принято не корректное сообщение
                except IncorrectDataRecivedError:
                    LOGGER.error(f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        LOGGER.critical(f'Потеряно соединение с сервером')
                        break
                # Проблемы с соединением
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError):
                    LOGGER.critical('Соединение с сервером прервано!')
                    break
                else:
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
                        # Захватываем работу с базой данных и сохраняем в нее сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.account_name, message[MESSAGE_TEXT])
                            except:
                                LOGGER.error('Ошибка взаимодействия с БД')
                            LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                        f'\n{message[MESSAGE_TEXT]}')
                    else:
                        LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')



# Функция генерирует запрос о присутствии клиента

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



# Функционал:
# - запрос контакт-листа
def contact_list_request(sock, name):
    LOGGER.debug(f'Запрос списка контактов для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    LOGGER.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    LOGGER.debug(f'Получен ответ {ans}')
    if RESPONSE in ans \
            and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# - запрос списка известных пользователей
def user_list_request(sock, username):
    LOGGER.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        USER: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans \
            and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# - добавление пользователя в контакт-лист
def add_contact(sock, username, contact):
    LOGGER.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    LOGGER.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print(f'Контакт {contact} создан успешно!')


# - удаление пользователя из контакт-листа
def remove_contact(sock, username, contact):
    LOGGER.debug(f'Удаление контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления контакта')
    print(f'Контакт {contact} удален успешно!')


def database_load(sock, database, username):
    # загружаем список известных пользователей
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        LOGGER.error('Ошибка запроса списка пользователей')
    else:
        database.add_users(users_list)

    # загружаем список известных пользователей
    try:
        contacts_list = contact_list_request(sock, username)
    except ServerError:
        LOGGER.error('Ошибка запроса списка контактов')
    else:
        for contact in contacts_list:
            database.add_contact(contact)



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
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_name}')
    try:

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.settimeout(1)  # необходим для освобождения сокета
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

        # Инициализация БД
        database = ClientDB(client_name)
        database_load(transport, database, client_name)


        # Если соединение с сервером установлено корректно,
        # запускаем отправку сообщений и взаимодействие с пользователем.
        module_sender = ClientSender(client_name, transport, database)
        module_sender.daemon = True
        module_sender.start()
        LOGGER.debug('Запущены процессы...')
        # запускаем клиентский процесс приема сообщений.
        receiver = ClientReader(client_name, transport, database)
        receiver.daemon = True
        receiver.start()

        while True:
            time.sleep(1)
            if receiver.is_alive() and module_sender.is_alive():
                continue
            break



if __name__ == '__main__':
    main()
