""" серверная часть """
import json
import socket
import sys

from common.prgm_utils import codecs_msg, send_message


# команда запуска для терминала:  python server.py -p [port] -a [addr]


def port():
    # функция определяет номер порта
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = 7777
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('После параметра -\'p\' указывается номер порта.')
        sys.exit(1)
    except ValueError:
        print(
            'Порт - это число в диапазоне от 1024 до 65535.')
        sys.exit(1)
    return listen_port


def addr():
    # Определяет ip-адрес
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''
    except IndexError:
        print(
            'После параметра \'a\'- адрес, который будет слушать сервер.')
        sys.exit(1)
    return listen_address


# формирует ответ на сообщение клиента
def parse_client_message(message):
    if 'action' in message \
            and message['action'] == 'presence' \
            and 'time' in message \
            and 'user' in message \
            and message['user']['account_name'] == 'Guest':
        return {'response': 200}
    return {
        'response': 400,
        'error': 'Bad Request'
    }


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((addr(), port()))

    server.listen(5)

    while True:
        client, client_address = server.accept()
        try:
            message_from_client = codecs_msg(client)  # получает сообщение от клиента
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
