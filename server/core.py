import binascii
import hmac
import json
import os
import select
import socket
import threading

from common.decos import login_required
from common.prgm_utils import get_message, send_message
from common.variables import *
from common.descripors import Port


class MessageProcessor(threading.Thread):
    """
    Основной класс сервера.
    Принимает соединения, словари - пакеты от клиентов.
    Обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока
    """
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        # Параметры подключения:
        self.addr = listen_address
        self.port = listen_port
        # База данных сервера
        self.database = database
        # Сокет, через который будет осуществляться работа
        self.sock = None
        # Список подключенных клиентов:
        self.clients = []
        # Сокеты:
        self.listen_sockets = None
        self.error_sockets = None
        # Флаг продолжения работы
        self.running = True
        # Словарь {имя: сокет}
        self.names = dict()
        # Конструктор предка
        super().__init__()

    def run(self):
        # Инициализируем сокет:
        self.init_socket()
        while self.running:
            # Ждем подключения, если таймаут вышел - ловим исключение
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Установлено соедение с клиентом: {client_address}')
                client.settimeout(5)
                self.clients.append(client)

                recv_data = []
                send_data = []
                err = []
                # Проверяем на наличие ожидающих клиентов
                try:
                    if self.clients:
                        recv_data, send_data, err = select.select(self.clients,
                                                                  self.clients,
                                                                  [],
                                                                  0)
                except OSError as err:
                    LOGGER.error(f'Ошибка работы с сокетами: {err}')

                # Принимаем сообщения и если ошибка, исключаем клиента
                if recv_data:
                    for client_with_message in recv_data:
                        try:
                            self.parse_client_message(get_message(client_with_message),
                                                      client_with_message)
                        except (OSError, json.JSONDecodeError, TypeError) as err:
                            # Ищем клиента в словаре клиентов и удаляем его из него
                            LOGGER.debug('Getting data from client exception', exc_info=err)
                            self.remove_client(client_with_message)

    def remove_client(self, client):
        """
        Метод - обработчик клиента, с которым прервана связь.
        Ищет клиенты и удаляет его из списков и базы:
        :param client:
        :return:
        """
        LOGGER.info(f'Клиент {client.getpeername} отключился от сервера')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        LOGGER.info(f'Запущен сервер, порт для подключений: {self.port}, '
                    f'адрес: {self.addr}. '
                    f'Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        # Слушаем сокет
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):
        """Функция адресной отправки сообщения определенному клиенту.
        Принимает словарь-сообщение,
        список зарегестрированных пользователей и
        слушающие сокеты.
        Ничего не возвращает
        :param message:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in self.names \
                and self.names[message[DESTINATION]] in self.listen_sockets:
            try:
                send_message(self.names[message[DESTINATION]], message)
                LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                            f'от пользователя {message[SENDER]}.')
            except OSError:
                self.remove_client(message[DESTINATION])
        elif message[DESTINATION] in self.names \
                and self.names[message[DESTINATION]] not in self.listen_sockets:
            LOGGER.error(f'Связь с клиентом {message[DESTINATION]}'
                         f'была потеряна. Соединение завершено, доставка не возможна.')
            self.remove_client(self.names[message[DESTINATION]])
        else:
            LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                         f'отправка сообщений не возможна.')

    @login_required
    def parse_client_message(self, message, client):
        """ Обработчик сообщений от клиентов,
        принимает словарь-сообщение от клиента,
        проверяет корректность,
        отправляет словарь-ответ, в случае необходимости
        :param message:
        :param client:
        :return:
        """
        LOGGER.debug(f'Разбор сообщения от клиента: {message}')
        # Если сообщение о присутствии, принимаем и отвечаем
        if ACTION in message \
                and message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            # Если сообщение о присутствии, то вызываем функцию авторизации.
            self.authorize_user(message, client)
        # Если это сообщение, то отправляем получателю.
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message \
                and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, OK_DICT)
                except OSError:
                    self.remove_client(client)
            else:
                response = ERR_DICT
                response[ERROR] = 'Пользователь не зарегистрирован на сервере'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        # Если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)

        # Если это запрос контакт-листа
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если это добавление контакта
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, OK_DICT)
            except OSError:
                self.remove_client(client)

        # Если это удаление контакта
        elif ACTION in message \
                and message[ACTION] == REMOVE_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, OK_DICT)
            except OSError:
                self.remove_client(client)

        # Если это запрос известных пользователей
        elif ACTION in message \
                and message[ACTION] == USERS_REQUEST \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        # Если это запрос публичного ключа пользователя
        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            # может быть, что ключа еще нет (если пользователь никогда не логинимся, отправляем 400)
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = ERR_DICT
                response[ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        # иначе ответ 400 Bad Request
        else:
            response = ERR_DICT
            response[ERROR] = 'Некорректный запрос'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def authorize_user(self, message, sock):
        """
        Метод реализующий авторизацию пользователей
        :param message:
        :param sock:
        :return:
        """
        LOGGER.debug(f'Start auth process for {message[USER]}')
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = ERR_DICT
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                LOGGER.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                LOGGER.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        # Проверяем что пользователь зарегистрирован на сервере
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = ERR_DICT
            response[ERROR] = 'Пользователь не зарегистрирован'
            try:
                LOGGER.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            LOGGER.debug('Correct username, starting passwd check')
            message_auth = RESPONSE_511
            # набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))

            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]),
                            random_str,
                            'MD5')
            digest = hash.digest()
            LOGGER.debug(f'Auth message = {message_auth}')
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                LOGGER.debug('Error in auth, data: ', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            if RESPONSE in ans \
                    and ans[RESPONSE] == 511 \
                    and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, OK_DICT)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])

                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY]
                )
            else:
                response = ERR_DICT
                response[ERROR] = 'Неверный пароль'
                try:
                    send_message(sock,response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """
        Метод, релизующий отправку сервисного сообщения 205 клиентам
        :return:
        """
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
