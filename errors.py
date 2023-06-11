"""Ошибки"""


class IncorrectDataRecivedError(Exception):
    """
    Исключение  - некорректные данные получены от сокета
    """
    def __str__(self):
        return 'Принято некорректное сообщение от удалённого компьютера.'


class NonDictInputError(Exception):
    """
    Исключение - аргумент функции не словарь
    """
    def __str__(self):
        return 'Аргумент функции должен быть словарём.'


class NonBytesInputError(Exception):
    """
    Исключение - аргумент функции не байты
    """
    def __str__(self):
        return 'Аргумент функции должен быть в байтах.'


class ReqFieldMissingError(Exception):
    """ Ошибка - отсутствует обязательное поле в принятом presence сообщении  """
    def __init__(self, req_field):
        self.req_field = req_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.req_field}.'

