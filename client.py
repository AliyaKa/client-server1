"""клиентская часть"""
import argparse

from PyQt5.QtWidgets import QApplication

from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from client.client_database import ClientDB
from common.decos import log
from common.errors import ServerError
from common.variables import *


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


if __name__ == '__main__':
    # загружаем параметры командной строки
    server_address, server_port, client_name = create_arg_parser()

    # Создаем клиентское приложение
    client_app = QApplication(sys.argv)

    # если имя пользователя не задано, запросим пользователя.
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)
    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, режим работы: {client_name}')

    database = ClientDB(client_name)

    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as err:
        print(err.text)
        exit(1)
    transport.daemon = True
    transport.start()

# Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Chat - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()
