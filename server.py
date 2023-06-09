""" серверная часть """
import argparse
import configparser
import os.path
import select
import socket
import threading


from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox


from common.variables import *
from common.prgm_utils import get_message, send_message
from common.decos import log
from descripors import Port
from metaclasses import ServerMaker
from server_database import ServerStorage
from server_gui import MainWindow, gui_create_model, ConfigWindow, HistoryWindow, create_stat_model

# Флаг - подключён новый пользователь
new_connection = False
conflag_lock = threading.Lock()



# Парсер аргументов командной строки:

@log
def create_arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


# Основной класс сервера
class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        # Параметры подключения:
        self.addr = listen_address
        self.port = listen_port
        # База данных сервера
        self.database = database
        # Список подключенных клиентов:
        self.clients = []
        # Список сообщений на отправку:
        self.messages = []
        # Словарь {имя: сокет}
        self.names = dict()
        # Конструктор предка
        super().__init__()

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
        self.sock.listen()

    def run(self):
        # Инициализируем сокет:
        global new_connection
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Установлено соедение с клиентом: {client_address}')
                self.clients.append(client)
            recv_data = []
            send_data = []
            err = []

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
                    except (OSError):
                        # Ищем клиента в словаре клиентов и удаляем его из него
                        LOGGER.info(f'Клиент {client_with_message.getpeername()}'
                                    f' отключился от сервера')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
                        with conflag_lock:
                            new_connection = True

            # Если есть сообщения, обрабатываем каждое
            for message in self.messages:
                try:
                    self.process_message(message, send_data)
                except (ConnectionAbortedError,
                        ConnectionError,
                        ConnectionResetError,
                        ConnectionRefusedError):
                    LOGGER.info(f'Связь с клиентом {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
                    with conflag_lock:
                        new_connection = True
            self.messages.clear()

    def process_message(self, message, listen_socks):
        """Функция адресной отправки сообщения определенному клиенту.
        Принимает словарь-сообщение,
        список зарегестрированных пользователей и
        слушающие сокеты.
        Ничего не возвращает
        :param message:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                        f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                         f'отправка сообщений не возможна.')

    def parse_client_message(self, message, client):
        """ Обработчик сообщений от клиентов,
        принимает словарь-сообщение от клиента,
        проверяет корректность,
        отправляет словарь-ответ, в случае необходимости
        :param message:
        :param client:
        :return:
        """
        global new_connection
        LOGGER.debug(f'Разбор сообщения от клиента: {message}')
        # Если сообщение о присутствии, принимаем и отвечаем
        if ACTION in message \
                and message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            # Если пользователь не зарегистрирован, регистрируем
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, OK_DICT)
                with conflag_lock:
                    new_connection = True
            # иначе отправляем ответ и завершаем соединение
            else:
                response = ERR_DICT
                response[ERROR] = 'Имя пользователя занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        # Если это сообщение, добавляем его в очередь сообщений.
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message \
                and self.names[message[SENDER]] == client:
            self.messages.append(message)
            self.database.process_message(message[SENDER], message[DESTINATION])
            return

        # Если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            LOGGER.info(f'Клиент {message[ACCOUNT_NAME]} корректно отключился от сервера.')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        # Если это запрос контакт-листа
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        # Если это добавление контакта
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, OK_DICT)

        # Если это удаление контакта
        elif ACTION in message \
                and message[ACTION] == REMOVE_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, OK_DICT)

        # Если это запрос известных пользователей
        elif ACTION in message \
                and message[ACTION] == USERS_REQUEST \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client, response)

        # иначе ответ 400 Bad Request
        else:
            response = ERR_DICT
            response[ERROR] = 'Некорректный запрос'
            send_message(client, response)
            return


def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    config = config_load()

    # Загрузка параметров командной строки (либо по умолчанию)
    listen_address, listen_port = create_arg_parser(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_address']
    )

    # Инициализация БД
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создает окно с настройками сервера.
    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_button.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_button.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()



if __name__ == '__main__':
    main()
