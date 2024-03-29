import base64
import json

from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox

from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from client.main_window_conv import Ui_MainClientWindow
from common.variables import LOGGER, MESSAGE_TEXT, SENDER
from common.errors import ServerError


class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport, keys):
        super().__init__()
        self.database = database
        self.transport = transport

        self.decrypter = PKCS1_OAEP.new(keys)

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # Кнопка Выход
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка Отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # Кнопка и пункт меню "Добавить" контакт
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Кнопка и пункт меню "Удалить" контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_remove_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Дабликлик по листу контактов
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)
        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        self.ui.label_3.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()
        self.ui.btn_clr.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    # История сообщений
    def history_list_update(self):
        history_list = sorted(self.database.get_history(self.current_chat),
                              key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        length = len(history_list)
        start_idx = 0
        if length > 20:
            start_idx = length - 20
        for i in range(start_idx, length):
            item = history_list[i]
            if item[1] == 'in':
                msg = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                msg.setEditable(False)
                msg.setBackground(QBrush(QColor(255, 200, 200)))
                msg.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(msg)
            else:
                msg = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                msg.setEditable(False)
                msg.setBackground(QBrush(QColor(200, 255, 200)))
                msg.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(msg)
        self.ui.list_messages.scrollToBottom()

    # Функционал:
    # - обработчик дабликлика по контакту
    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    # - устанавливает активного собеседника
    def set_active_user(self):
        try:
            self.current_chat_key = self.transport.key_request(self.current_chat)
            LOGGER.debug(f'Загружен открытый ключ для {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            LOGGER.debug(f'Не удалось получить ключ для {self.current_chat}')

        if not self.current_chat_key:
            self.messages.warning(self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return

        self.ui.label_3.setText(f'Введите сообщение для {self.current_chat}: ')
        self.ui.btn_clr.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.history_list_update()

    # - обновление контакт-листа
    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # - добавление контакта
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            LOGGER.info(f'Контакт {new_contact} успешно добавлен')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен')

    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        else:
            self.database.add_contact(selected)
            self.clients_list_update()
            LOGGER.info(f'Контакт {selected} успешно удален')
            self.messages.information(self, 'Успех', 'Контакт успешно удален')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        message_text_encrypted = self.encryptor.encrypt(message_text.encode('utf-8'))
        message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)
        try:
            self.transport.send_message(self.current_chat, message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Соединение с сервером потеряно')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            LOGGER.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    # Слот приёма нового сообщений
    @pyqtSlot(dict)
    def message(self, message):
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(self, 'Ошибка', 'Не удалось декодировать сообщение.')
            return
        self.database.save_message(
            self.current_chat,
            'in',
            decrypted_message.decode('utf-8')
        )
        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.database.check_contact(sender):
                if self.messages.question(self,
                                          'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}.\n '
                                          f'Данного пользователя нет в вашем контакт-листе.\n '
                                          f'Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.database.save_message(self.current_chat,
                                               'in',
                                               decrypted_message.decode('utf-8'))
                    self.set_active_user()

    # Слот потери соединения.
    # Выдаёт сообщение об ошибке и завершает работу приложения
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    @pyqtSlot()
    def sig_205(self):
        """
        Слот выполняющий обновление баз данных по команде сервера.
        """
        if self.current_chat and not self.database.check_user(self.current_chat):
            self.messages.warning(
                self,
                'Сочувствую',
                'К сожалению собеседник был удалён с сервера.')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
        trans_obj.message_205.connect(self.sig_205)



