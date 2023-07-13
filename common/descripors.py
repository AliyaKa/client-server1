import logging

logger = logging.getLogger('server')


# Дескриптор для описания порта
class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(f'Сервер не может быть запущен с указанием порта {value}. '
                            f'Допустимые адреса с 1024 до 65535.')
            raise TypeError('Не корректный номер порта')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
