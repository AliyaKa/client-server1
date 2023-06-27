""" серверная часть """
import argparse
import select
import socket
import sys
from common.variables import *
from common.prgm_utils import get_message, send_message
from decos import log
from descripors import Port
from metaclasses import ServerMaker


# Парсер аргументов командной строки:
@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


# Основной класс сервера
class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port):
        # Параметры подключения:
        self.addr = listen_address
        self.port = listen_port
        # Список подключенных клиентов:
        self.clients = []
        # Список сообщений на отправку:
        self.messages = []
        # Словарь {имя: сокет}
        self.names = dict()

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

    def main_loop(self):
        # Инициализируем сокет:
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
                    recv_data, send_data, err = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data:
                for client_with_message in recv_data:
                    try:
                        self.parse_client_message(get_message(client_with_message),
                                                  client_with_message)
                    except:
                        LOGGER.info(f'Клиент {client_with_message.getpeername()}'
                                    f' отключился от сервера')
                        self.clients.remove(client_with_message)
            for message in self.messages:
                try:
                    self.process_message(message, send_data)
                except:
                    LOGGER.info(f'Связь с клиентом {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
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
        LOGGER.debug(f'Разбор сообщения от клиента: {message}')
        # Если сообщение о присутствии, принимаем и отвечаем
        if ACTION in message \
                and message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            # Если пользователь не зарегистрирован, регистрируем
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, OK_DICT)
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
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # иначе ответ 400 Bad Request
        else:
            response = ERR_DICT
            response[ERROR] = 'Некорректный запрос'
            send_message(client, response)
            return


def main():
    listen_address, listen_port = create_arg_parser()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
