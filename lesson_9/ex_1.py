"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""
import subprocess
from ipaddress import ip_address


def host_ping(hosts):
    results = {'Reachable': '', 'Unreachable': ''}
    for host in hosts:
        try:
            host = ip_address(host)
        except ValueError:
            pass
        ping = subprocess.Popen(["ping", "-w", "5", f'{host}'], stdout=subprocess.PIPE, shell=False)
        ping.wait()
        if ping.returncode == 0:
            msg = f'{host} - Узел доступен'
            results['Reachable'] += f"{str(host)}\n"
        else:
            msg = f'{host} - Узел недоступен'
            results['Unreachable'] += f"{str(host)}\n"
        print(msg)
    return results


if __name__ == '__main__':
    ip_addresses = ['yandex.ru', '127.0.0.1', '192.168.0.100', '192.168.0.97']
    host_ping(ip_addresses)

#  Результат
# yandex.ru - Узел доступен
# 127.0.0.1 - Узел доступен
# 192.168.0.100 - Узел недоступен
# 192.168.0.97 - Узел доступен
