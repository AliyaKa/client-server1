import subprocess
import time
from tkinter import Entry, Button, Tk, Label, StringVar

from common.variables import DEFAULT_IP, DEFAULT_PORT


class Launcher:

    def __init__(self, master):
        self.master = master
        master.title('Launcher')
        master.geometry('400x200+700+300')

        self.host = StringVar()
        self.port = StringVar()
        self.clients = StringVar()

        self.host_label = Label(master, text='host:')
        self.port_label = Label(master, text='port:')
        self.clients_label = Label(master, text='clients:')

        self.host_label.grid(row=0, column=0, sticky="w")
        self.port_label.grid(row=1, column=0, sticky="w")
        self.clients_label.grid(row=2, column=0, sticky="w")

        self.host_entry = Entry(textvariable=self.host)
        self.port_entry = Entry(textvariable=self.port)
        self.clients_entry = Entry(textvariable=self.clients)

        self.host_entry.insert(0, DEFAULT_IP)
        self.port_entry.insert(0, DEFAULT_PORT)
        self.clients_entry.insert(0, 3)

        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        self.port_entry.grid(row=1, column=1, padx=5, pady=5)
        self.clients_entry.grid(row=2, column=1, padx=5, pady=5)

        self.start_button = Button(text="Запуск", command=lambda: self.start())
        self.stop_button = Button(text="Закрыть все окна", command=lambda: self.stop())

        self.start_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")
        self.stop_button.grid(row=3, column=2, padx=5, pady=5, sticky="e")

        self.processes = []

    def start(self):
        self.processes.append(
            subprocess.Popen(f'gnome-terminal -e "python server.py -p {self.port.get()} -a {self.host.get()}"',
                             stdout=subprocess.PIPE,
                             stderr=None,
                             shell=True))
        time.sleep(0.1)

        for i in range(int(self.clients.get())):
            self.processes.append(subprocess.Popen(
                f'gnome-terminal -e "python client.py {self.host.get()} {self.port.get()} -n test{i + 1}"',
                stdout=subprocess.PIPE,
                stderr=None,
                shell=True))
            time.sleep(0.1)

    def stop(self):
        while self.processes:
            victim = self.processes.pop()
            victim.kill()


root = Tk()
my_gui = Launcher(root)
root.mainloop()
