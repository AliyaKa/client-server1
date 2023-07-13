
import subprocess


PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        clients = int(input('Введите количество тестовых клиентов для запуска: '))

        PROCESS.append(subprocess.Popen('gnome-terminal -e "python server.py"',
                                        stdout=subprocess.PIPE,
                                        stderr=None,
                                        shell=True
                                        ))

        for i in range(clients):
            PROCESS.append(subprocess.Popen(f'gnome-terminal -e "python client.py -n test{i+1}"',

                                            stdout=subprocess.PIPE,
                                            stderr=None,
                                            shell=True
                                            ))

    elif ACTION == 'x':
        while PROCESS:
            PROCESS.pop().kill()
