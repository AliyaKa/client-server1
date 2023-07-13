import dis


# Метакласс для проверки соответствия сервера
class ServerMaker(type):
    def __init__(self, clsname, bases, clsdict):
        # clsname - экземпляр метакласса Server
        # bases - кортеж базовых классов
        # clsdict - словарь атрибутов и методов экземпляра метакласса

        # Список методов, которые используются в функциях класса:
        methods = []
        # Атрибуты, которые используются в функциях класса:
        attrs = []
        # Перебираем ключи
        for func in clsdict:
            try:
                # Возвращает итератор по инструкциям в предоставленной функции,
                # методе, строке исходного кода или объекте кода.
                ret = dis.get_instructions(clsdict[func])

            # Если не функция, ловим исключение:
            except TypeError:
                pass
            else:
                # Если функция - разбираем код, получаем используемые методы и атрибуты
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, используемыми в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, используемыми в функциях класса
                            attrs.append(i.argval)
        print(methods)
        # Если используется не допустимый метод connect, вызываем исключение
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')

        # Если сокет не инициализировался константами SOCK_STREAM(TCP), AF_INET(IPv4) - исключение
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Не корректная инициализация сокета.')
        # Вызываем конструктор предка
        super().__init__(clsname, bases, clsdict)


# Метакласс для проверки корректности клиентов:
class ClientMaker(type):
    def __init__(self, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование не допустимого метода')
            if 'get_message' in methods or 'send_message' in methods:
                pass
            else:
                raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
            super().__init__(clsname, bases, clsdict)
