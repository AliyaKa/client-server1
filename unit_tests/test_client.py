"""unittests для клиента"""
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import create_presence_msg, answer_server
import os
import sys
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestClass(unittest.TestCase):

    # Тест проверяющий создание коректного запроса
    def test_def_presence(self):
        test = create_presence_msg()
        test[TIME] = 1.1  # чтобы тест был пройден, присвоим значение времени принудительно
        self.assertEqual(test,
                         {
                             ACTION: PRESENCE,
                             TIME: 1.1,
                             USER: {
                                 ACCOUNT_NAME: 'Guest'
                             }
                         })

    # Тест проверяющий разбор ответа сервера 200
    def test_200_ans(self):
        self.assertEqual(answer_server({RESPONSE: 200}), '200 : OK')

    # Тест проверяющий разбор ответа сервера 400
    def test_400_ans(self):
        self.assertEqual(answer_server(
            {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            }
        ), '400 : Bad Request')

    # Тест исключения без поля RESPONSE
    def test_no_response(self):
        self.assertRaises(ValueError, answer_server, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
