"""unittests для сервера"""
from common.variables import TIME, USER, ACCOUNT_NAME,\
    ACTION, PRESENCE, ERR_DICT, OK_DICT
from server import parse_client_message
import os
import sys
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestServer(unittest.TestCase):
    ok = OK_DICT
    err = ERR_DICT

    # корректный запрос
    def test_ok(self):
        self.assertEqual(parse_client_message(
            {
                ACTION: PRESENCE,
                TIME: 1.1,
                USER: {
                    ACCOUNT_NAME: 'Guest'
                }
            }
        ), self.ok)

    # ошибка если нет действия
    def test_no_action(self):
        self.assertEqual(parse_client_message(
            {
                TIME: 1.1,
                USER: {
                    ACCOUNT_NAME: 'Guest'
                }
            }
        ),
            self.err)

    # ошибка если запрос не содержит штампа времени
    def test_no_time(self):
        self.assertEqual(parse_client_message(
            {
                ACTION: PRESENCE,
                USER: {ACCOUNT_NAME: 'Guest'}
            }
        ),
            self.err)

    # ошибка если нет пользователя
    def test_no_user(self):
        self.assertEqual(parse_client_message(
            {
                ACTION: PRESENCE,
                TIME: 1.1
            }
        ),
            self.err)

    # ошибка в имени пользователя"""
    def test_unknown_user(self):
        self.assertEqual(parse_client_message(
            {
                ACTION: PRESENCE,
                TIME: 1.1,
                USER: {ACCOUNT_NAME: 'Aliya'}}
        ),
            self.err)


if __name__ == '__main__':
    unittest.main()
