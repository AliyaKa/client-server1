""" серверная часть """
import argparse
import select
import socket
import sys
from common.variables import DEFAULT_PORT, PRESENCE, ACTION, TIME, \
    USER, ACCOUNT_NAME, MAX_CONNECTIONS, ERR_DICT, LOGGER, MESSAGE, \
    MESSAGE_TEXT, SENDER, OK_DICT, ERROR, DESTINATION, EXIT
from common.prgm_utils import get_message, send_message
from decos import log


@log
def parse_client_message(message, messages_list, client, clients, names):
    """ Обработчик сообщений от клиентов,
    принимает словарь-сообщение от клиента,
    проверяет корректность,
    отправляет словарь-ответ, в случае необходимости
    :param message:
    :param messages_list:
    :param client:
    :param clients:
    :param names:
    :return:
    """
    LOGGER.debug(f'Разбор сообщения от клиента: {message}')
    # Если сообщение о присутствии, принимаем и отвечаем
    if ACTION in message \
            and message[ACTION] == PRESENCE \
            and TIME in message \
            and USER in message:
        # Если пользователь не зарегистрирован, регистрируем
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, OK_DICT)
        # иначе отправляем ответ и завершаем соединение
        else:
            response = ERR_DICT
            response[ERROR] = 'Имя пользователя занято.'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    # Если это сообщение, добавляем его в очередь сообщений.
    elif ACTION in message \
            and message[ACTION] == MESSAGE \
            and DESTINATION in message \
            and TIME in message \
            and SENDER in message \
            and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    # Если клиент выходит
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return
    # иначе ответ 400 Bad Request
    else:
        response = ERR_DICT
        response[ERROR] = 'Некорректный запрос'
        send_message(client, response)
        return


@log
def process_message(message, names, listen_socks):
    """Функция адресной отправки сообщения определенному клиенту.
    Принимает словарь-сообщение,
    список зарегестрированных пользователей и
    слушающие сокеты.
    Ничего не возвращает
    :param message:
    :param names:
    :param listen_socks:
    :return:
    """
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                    f'от пользователя {message[SENDER]}.')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        LOGGER.error(f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                     f'отправка сообщений не возможна.')


@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    if listen_port < 1024 or listen_port > 65535:
        LOGGER.critical(f'Попытка запуска сервера с порта {listen_port}. '
                        f'Допустимы порты с 1024 до 65535.')
        sys.exit(1)
    return listen_address, listen_port


@log
def main():
    # определение порта
    listen_address, listen_port = create_arg_parser()
    LOGGER.info(f'Запущен сервер, порт для подключений: {listen_port}, '
                f'адрес: {listen_address}. '
                f'Если адрес не указан, принимаются соединения с любых адресов.')
    # Сокет
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((listen_address, listen_port))
    server.settimeout(0.5)
    # Слушаем порт
    server.listen(MAX_CONNECTIONS)

    # список клиентов и очередь сообщений
    clients = []
    messages = []

    names = dict()  # Словарь с именами пользователей и соответствующими им сокетами

    while True:
        try:
            client, client_address = server.accept()
        except OSError:
            pass
        else:
            LOGGER.info(f'Установлено соедение с клиентом: {client_address}')
            clients.append(client)
        recv_data = []
        send_data = []
        err = []

        try:
            if clients:
                recv_data, send_data, err = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if recv_data:
            for client_with_message in recv_data:
                try:
                    parse_client_message(get_message(client_with_message),
                                         messages,
                                         client_with_message,
                                         clients,
                                         names)
                except:
                    LOGGER.info(f'Клиент {client_with_message.getpeername()}'
                                f' отключился от сервера')
                    clients.remove(client_with_message)
        for i in messages:
            try:
                process_message(i, names, send_data)
            except Exception:
                LOGGER.info(f'Связь с клиентом {i[DESTINATION]} была потеряна')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()


if __name__ == '__main__':
    main()
