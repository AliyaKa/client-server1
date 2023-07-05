import sys

from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QLabel, QTableView, QLineEdit, QFileDialog, QPushButton, \
    QDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt


def gui_create_model(database):
    list_users = database.active_users_list()
    model_list = QStandardItemModel()
    model_list.setHorizontalHeaderLabels(['Имя клиента', 'IP адрес', 'Порт', 'Время подключения'])
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
    return model_list


def create_stat_model(database):
    history_list = database.message_history()
    model_list = QStandardItemModel()
    model_list.setHorizontalHeaderLabels([
        'Имя клиента',
        'Последний вход',
        'Отправлено сообщений',
        'Получено сообщений'
    ])
    for row in history_list:
        user, last_seen, send, recv = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        send = QStandardItem(str(send))
        send.setEditable(False)
        recv = QStandardItem(str(recv))
        recv.setEditable(False)
        model_list.appendRow([user, last_seen, send, recv])
    return model_list


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.statusBar()
        self.toolbar = self.addToolBar('MainBar')

        self.refresh_button = QAction('Обновить список', self)
        self.toolbar.addAction(self.refresh_button)

        self.config_button = QAction('Настройки сервера', self)
        self.toolbar.addAction(self.config_button)

        self.show_history_button = QAction('История клиентов', self)
        self.toolbar.addAction(self.show_history_button)

        exitButton = QAction('Выход', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(qApp.quit)
        self.toolbar.addAction(exitButton)

        # Настройки окна
        self.setFixedSize(800, 600)
        self.setWindowTitle('Сервер мессенджера')

        # Надпись
        self.label = QLabel('Список клиентов, подключенных к серверу:', self)
        font = self.label.font()
        font.setBold(True)
        #font.setItalic(True)
        self.label.setFont(font)
        self.label.setFixedSize(350, 30)
        self.label.move(15, 25)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(20, 60)
        self.active_clients_table.setFixedSize(780, 400)

        desktop = QtWidgets.QApplication.desktop()
        x = (desktop.width() - self.width()) // 2
        y = (desktop.height() - self.height()) // 2
        self.move(x, y)

        self.show()


# Класс окна с историей пользователей
class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


# Класс окна настроек
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setFixedSize(450, 260)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле БД:
        self.db_path_label = QLabel('Путь до базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(400, 15)

        # Строка путь БД
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(300, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(350, 28)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Надпись "Имя файла базы данных"
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(350, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(230, 20)

        # Надпись "номер порта"
        self.port_label = QLabel('Номер порта:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(400, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(100, 20)
        #
        # Надпись "IP адрес"
        self.ip_label = QLabel('IP адрес:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.setToolTip('оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.')
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        # Кнопка сохранения настроек
        self.save_button = QPushButton('Сохранить', self)
        self.save_button.move(150, 190)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(235, 190)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    message = QMessageBox
    dial = ConfigWindow()

    app.exec_()
