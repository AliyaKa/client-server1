"""Клиентская часть"""
import argparse
import os.path

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox


from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from client.transport import ClientTransport
from client.client_database import ClientDB
from common.decos import log
from common.errors import ServerError
from common.variables import *


@log
def create_arg_parser():
    """
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов
    адрес сервера, порт, имя пользователя, пароль.
    Выполняет проверку на корректность номера порта.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')

    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])

    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password


    if not 1023 < server_port < 65536:

        LOGGER.critical(
            f' Попытка запуска клиента с зарезервированным номером порта: {server_port}.'
            f' Допустимы порты с 1024 до 65535.')
        sys.exit(1)


    return server_address, server_port, client_name, client_passwd



if __name__ == '__main__':

    # загружаем параметры командной строки
    server_address, server_port, client_name, client_passwd = create_arg_parser()
    LOGGER.debug('Args loaded')

    # Создаем клиентское приложение
    client_app = QApplication(sys.argv)

    # если имя пользователя не задано, запросим пользователя.
    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        # Если пользователь ввел имя и нажал ОК,
        # сохраняем введенное имя и удаляем объект, иначе выход
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            LOGGER.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}')
        else:
            exit(0)
    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port},  имя пользователя: {client_name}')
    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    LOGGER.debug('Keys successfully loaded')
    database = ClientDB(client_name)
    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
        LOGGER.debug('Transport ready')
    except ServerError as err:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', err.text)
        exit(1)
    transport.daemon = True
    transport.start()

    del start_dialog

# Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Chat - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()

