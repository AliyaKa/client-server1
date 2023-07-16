import sys

from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView, \
    QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer

from server.add_user import RegisterUser
from server.config_window import ConfigWindow
from server.remove_user import DelUserDialog
from server.stat_window import StatWindow


class MainWindow(QMainWindow):
    """Класс - основное окно сервера"""

    def __init__(self, database, server, config):
        super().__init__()
        self.database = database
        self.server_thread = server
        self.config = config
        self.exitAction = QAction('Выход', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(qApp.quit)

        self.refresh_button = QAction('Обновить список', self)
        self.config_button = QAction('Настройки сервера', self)
        self.register_button = QAction('Регистрация пользователя', self)
        self.remove_button = QAction('Удалить пользователя', self)
        self.show_history_button = QAction('История клиента', self)

        self.statusBar()
        self.statusBar().showMessage('Server Working...')

        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)
        self.toolbar.addAction(self.register_button)
        self.toolbar.addAction(self.remove_button)

        # Настройки окна
        self.setFixedSize(800, 600)
        self.setWindowTitle('Сервер мессенджера')

        # Надпись
        self.label = QLabel('Список клиентов, подключенных к серверу:', self)
        font = self.label.font()
        font.setBold(True)
        # font.setItalic(True)
        self.label.setFont(font)
        self.label.setFixedSize(350, 30)
        self.label.move(15, 25)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(20, 60)
        self.active_clients_table.setFixedSize(780, 400)

        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_button.triggered.connect(self.server_config)
        self.register_button.triggered.connect(self.reg_user)
        self.remove_button.triggered.connect(self.rem_user)

        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.width() - self.width()) // 2
        y = (desktop.height() - self.height()) // 2
        self.move(x, y)

        self.show()

    def create_users_model(self):
        """Метод заполняющий таблицу активных пользователей"""
        list_users = self.database.active_users_list()
        model_list = QStandardItemModel()
        model_list.setHorizontalHeaderLabels(
            ['Имя клиента', 'IP адрес', 'Порт', 'Время подключения'])
        for row in list_users:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            model_list.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(model_list)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        """Метод создающий окно со статистикой клиентов."""
        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def server_config(self):
        """Метод создающий окно с настройками сервера."""
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        """Метод создающий окно регистрации пользователя."""
        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):
        """Метод создающий окно удаления пользователя."""
        global rem_window
        rem_window = DelUserDialog(self.database, self.server_thread)
        rem_window.show()
