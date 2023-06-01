"""клиентская часть"""
import json
import socket
import sys
import time
from common.variables import DEFAULT_PORT, DEFAULT_IP, ACTION, TIME, USER, ACCOUNT_NAME,\
    PRESENCE, RESPONSE, ERROR
from common.prgm_utils import get_message, send_message

# команда запуска для терминала:  python client.py [addr] [port]


def create_presence_msg(account_name='Guest'):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return out


def answer_server(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


def main():

    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP
        server_port = DEFAULT_PORT
    except ValueError:
        print(
            'Порт - это число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_address, server_port))

    message_to_server = create_presence_msg()
    send_message(client, message_to_server)

    #  Получаем ответ
    try:
        answer = answer_server(get_message(client))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    main()
