import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from common.decos import log


@log
def get_message(client):
    # функция принимает ответ стороны
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@log
def send_message(sock, message):
    # функция отправляет ответ стороне
    json_message = json.dumps(message)
    encoded_message = json_message.encode(ENCODING)
    sock.send(encoded_message)



