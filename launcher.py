import subprocess
import time

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen('gnome-terminal -e "python server.py"',
                                        stdout=subprocess.PIPE,
                                        stderr=None,
                                        shell=True
                                        ))
        time.sleep(0.1)
        for i in range(3):
            PROCESS.append(subprocess.Popen(f'gnome-terminal -e "python client.py -n test{i}"',
                                            stdout=subprocess.PIPE,
                                            stderr=None,
                                            shell=True
                                            ))
            time.sleep(0.1)

    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
