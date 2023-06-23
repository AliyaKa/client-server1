"""Декораторы"""
import log.configs.server_log_config
import log.configs.client_log_config
from common.variables import LOGGER


def log(func_to_log):
    """Функция-декоратор"""

    def log_writer(*args, **kwargs):
        """Обертка"""
        ret = func_to_log(*args, **kwargs)
        LOGGER.debug(f'Функция {func_to_log.__name__} c параметрами {args}, {kwargs}. '
                     f'Вызов из модуля {func_to_log.__module__}. ')
        return ret
    return log_writer
