""" серверная часть """

import json
import socket
import sys
from common.variables import DEFAULT_PORT, RESPONSE, PRESENCE, ACTION, TIME,\
    USER, ACCOUNT_NAME, ERROR, MAX_CONNECTIONS
from common.prgm_utils import get_message, send_message


# команда запуска для терминала:  python server.py -p [port] -a [addr]

# формирует ответ на сообщение клиента
def parse_client_message(message):
    if ACTION in message \
            and message[ACTION] == PRESENCE \
            and TIME in message \
            and USER in message \
            and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }


def main():
    # определение порта
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('После параметра -\'p\' указывается номер порта.')
        sys.exit(1)
    except ValueError:
        print(
            'Порт - это число в диапазоне от 1024 до 65535.')
        sys.exit(1)
    # определение адреса
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        print(
            'После параметра \'a\'- адрес, который будет слушать сервер.')
        sys.exit(1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((listen_address, listen_port))

    server.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = server.accept()
        try:
            message_from_client = get_message(client)  # получает сообщение от клиента
            print(message_from_client)
            response = parse_client_message(message_from_client)  # формирует ответ клиенту
            send_message(client, response)  # отправляет ответ клиенту
            client.close()
            break
        except (ValueError, json.JSONDecodeError):
            print('Некорретное сообщение от клиента.')
            client.close()
            break


if __name__ == '__main__':
    main()
