import subprocess


PROCESS = []

while True:
    ACTION = input(
        'Выберите действие: q - выход, '
        's - запустить сервер, k запустить клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':

        PROCESS.append(subprocess.Popen('gnome-terminal -e "python server.py"',
                                        stdout=subprocess.PIPE,
                                        stderr=None,
                                        shell=True
                                        ))
    elif ACTION == 'k':
        clients_count = int(
            input('Введите количество тестовых клиентов для запуска: '))
        for i in range(clients_count):
            PROCESS.append(
                subprocess.Popen(
                    f'gnome-terminal -e "python client.py -n test{i+1} -p 123456"',
                    stdout=subprocess.PIPE,
                    stderr=None,
                    shell=True))
    elif ACTION == 'x':
        while PROCESS:
            PROCESS.pop().kill()
