import json
import socket
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal

from common.prgm_utils import send_message, get_message
from common.variables import *
from common.decos import log
from common.errors import ServerError

sys.path.append('../')

socket_lock = threading.Lock()


# Класс-транспорт, отвечающий за взаимодействие с сервером
class ClientTransport(threading.Thread, QObject):
    # Сигналы о новом сообщении и потере соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        # Вызовем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)


        self.database = database
        self.username = username
        self.transport = None
        self.connection_init(port, ip_address)
        # Обновим таблицы известных пользователей и их контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                LOGGER.critical('Потеряно соединение с сервером')
                raise ServerError('Потеряно соединение с сервером.')
            LOGGER.error('Таймаут соединения при обновлении списков пользователей')
        except json.JSONDecodeError:
            LOGGER.critical('Потеряно соединение с сервером')
            raise ServerError('Потеряно соединение с сервером.')
        self.running = True

    # Функция инициализации соединения с сервером
    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        # Соединяемся: у нас 5 попыток, в случае успеха флаг connected установим True
        connected = False
        for i in range(5):
            LOGGER.info(f'Попытка подключения № {i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)
        if not connected:
            LOGGER.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')
        LOGGER.debug('Установлено соединение с сервером')

        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            LOGGER.critical('Потеряно соединение с сервером')
            raise ServerError('Потеряно соединение с сервером.')
        LOGGER.info('Соединение с сервером успешно установлено.')

    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username
            }
        }
        LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.username}')
        return out

    @log
    def process_server_ans(self, message):
        if RESPONSE in message:
            LOGGER.debug(f'Разбор ответа сервера: {message}')
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                LOGGER.error(f'Ответ сервера 400 : {message[ERROR]}. Отсутствует обязательное поле')
                raise ServerError(f'400 : {message[ERROR]}')
            else:
                LOGGER.debug(f'Принят неизвестный код подтверждения {message[RESPONSE]}')
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and SENDER in message \
                and DESTINATION in message \
                and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.username:
            LOGGER.debug(f'Получено сообщение от пользователя {message[SENDER]}: {message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])

    def user_list_update(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            LOGGER.error('Не удалось обновить список известных пользователей')

    def contacts_list_update(self):
        LOGGER.debug(f'Запрос контакт-листа для пользователя {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOGGER.error('Не удалось обновить список контактов')

    def add_contact(self, contact):
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        LOGGER.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def transport_shutdown(self):
        self.running = False
        req = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_message(self.transport, req)
            except OSError:
                pass
        LOGGER.debug('Транспорт завершает работу')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            LOGGER.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        LOGGER.debug('Запущен процесс - приемник сообщений с сервера.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        LOGGER.critical('Соединение с сервером потеряно')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError,
                        TypeError):
                    LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    LOGGER.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
