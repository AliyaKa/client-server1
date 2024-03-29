import os.path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox


class ConfigWindow(QDialog):
    """Класс - окно настроек"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()

    def initUI(self):
        """Настройки окна"""
        self.setFixedSize(450, 260)
        self.setWindowTitle('Настройки сервера')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

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

        self.db_path_select.clicked.connect(self.open_file_dialog)

        self.show()

        self.db_path.insert(self.config['SETTINGS']['Database_path'])
        self.db_file.insert(self.config['SETTINGS']['Database_file'])
        self.port.insert(self.config['SETTINGS']['Default_port'])
        self.ip.insert(self.config['SETTINGS']['Listen_Address'])
        self.save_button.clicked.connect(self.save_server_config)

    def open_file_dialog(self):
        """Метод обработчик открытия окна выбора папки."""
        global dialog
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace('/', '\\')
        self.db_path.clear()
        self.db_path.insert(path)


    def save_server_config(self):
        """
        Метод - сохранение настроек. Проверяет правильность введенных данных.
        Если все верно, сохраняет в ini файл
        :return:
        """
        global config_window
        message = QMessageBox()
        self.config['SETTINGS']['Database_path'] = self.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['Listen_Address'] = self.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                dir_path = os.path.join(dir_path, '..')
                with open(f"{dir_path}/{'server.ini'}", "w") as conf:
                    self.config.write(conf)
                    message.information(self, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(self, 'Ошибка', 'Порт должен быть от 1024 до 65536')
