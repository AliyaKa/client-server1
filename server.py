""" серверная часть """
import argparse
import select
import socket
import sys
import time
from common.variables import DEFAULT_PORT, PRESENCE, ACTION, TIME, \
    USER, ACCOUNT_NAME, MAX_CONNECTIONS, ERR_DICT, LOGGER, MESSAGE, \
    MESSAGE_TEXT, RESPONSE, SENDER
from common.prgm_utils import get_message, send_message
from decos import log


@log
def parse_client_message(message, messages_list, client):
    LOGGER.debug(f'Разбор сообщения от клиента: {message}')
    if ACTION in message \
            and message[ACTION] == PRESENCE \
            and TIME in message \
            and USER in message \
            and message[USER][ACCOUNT_NAME] == 'Guest':
        send_message(client, {RESPONSE: 200})
        return
    elif ACTION in message \
            and message[ACTION] == MESSAGE \
            and TIME in message \
            and MESSAGE_TEXT in message:
        messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        return
    else:
        send_message(client, ERR_DICT)
        return


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

    server.listen(MAX_CONNECTIONS)

    # список клиентов и очередь сообщений
    clients = []
    messages = []

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
                                         client_with_message)
                except:
                    LOGGER.info(f'Клиент {client_with_message.getpeername()}'
                                f' отключился от сервера')
                    clients.remove(client_with_message)
        if messages and send_data:
            message = {
                ACTION: MESSAGE,
                SENDER: messages[0][0],
                TIME: time.time(),
                MESSAGE_TEXT: messages[0][1]
            }
            del messages[0]
            for waiting_client in send_data:
                try:
                    send_message(waiting_client, message)
                except:
                    LOGGER.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    clients.remove(waiting_client)


if __name__ == '__main__':
    main()
