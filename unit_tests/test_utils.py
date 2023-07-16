"""Unittests утилит"""
from common.variables import USER, ACCOUNT_NAME, TIME, \
        ACTION, PRESENCE, ENCODING, OK_DICT, ERR_DICT
from common.utils import get_message, send_message
import json
import os
import sys
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestSocket:

    """Тестовый класс для имитации работы функций"""

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode(ENCODING)


class Tests(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 1.1,
        USER: {
            ACCOUNT_NAME: 'Test'
        }
    }
    test_dict_recv_ok = OK_DICT
    test_dict_recv_err = ERR_DICT

    def test_send_message(self):
        """
        Тестируем корректность работы фукции отправки,
        создадим тестовый сокет и проверим корректность отправки словаря
        :return:
        """
        # экземпляр тестового словаря
        test_socket = TestSocket(self.test_dict_send)
        # вызов тестируемой функции, результаты будут сохранены в тестовом сокете
        send_message(test_socket, self.test_dict_send)
        # сравниваем результат довренного кодирования и результат от тестируемой функции
        self.assertEqual(test_socket.encoded_message, test_socket.received_message)
        # дополнительно, проверим генерацию исключения, при не корректном словаре на входе.
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)

    def test_get_message(self):
        """
        Тест функции приёма сообщения
        :return:
        """
        test_sock_ok = TestSocket(self.test_dict_recv_ok)
        test_sock_err = TestSocket(self.test_dict_recv_err)
        # тест корректной расшифровки корректного словаря
        self.assertEqual(get_message(test_sock_ok), self.test_dict_recv_ok)
        # тест корректной расшифровки ошибочного словаря
        self.assertEqual(get_message(test_sock_err), self.test_dict_recv_err)


if __name__ == '__main__':
    unittest.main()
