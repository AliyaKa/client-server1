"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса. По результатам проверки должно
выводиться соответствующее сообщение.
"""
import ipaddress
from ex_1 import host_ping


def check_ip(ip):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    else:
        return True


def host_range_ping():
    ip_list = []
    ip = input('Введите ip-адрес: ')
    s = input('Сколько адресов проверить? ')
    if check_ip(ip) and s.isnumeric():
        begin = ip.split('.')[0:3]
        last = ip.split('.')[3]
        if (int(last) + int(s)) <= 254:
            for i in range(0, int(s)):
                ip_list.append('.'.join(begin) + '.' + str(int(last) + i))
        else:
            print(f"Максимальное число хостов для проверки: {254-int(last)}")

    else:
        print('Вы ввели не корректные данные')
    return host_ping(ip_list)


if __name__ == "__main__":
    host_range_ping()


# Результат:

# Введите ip-адрес: 192.168.0.94
# Сколько адресов проверить? 7
# 192.168.0.94 - Узел недоступен
# 192.168.0.95 - Узел недоступен
# 192.168.0.96 - Узел недоступен
# 192.168.0.97 - Узел доступен
# 192.168.0.98 - Узел доступен
# 192.168.0.99 - Узел недоступен
# 192.168.0.100 - Узел недоступен
