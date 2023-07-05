from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, registry
from common.variables import *
import datetime

mapper_registry = registry()


# Класс - серверная БД
class ServerStorage:
    # Класс - отображение таблицы всех пользователей
    # Экземпляр класса = запись в таблице AllUsers
    class AllUsers:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    # Класс - отображение таблицы активных пользователей:
    # Экземпляр класса = запись в таблице ActiveUsers
    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    # Класс - отображение таблицы истории входов
    # Экземпляр класса = запись в таблице LoginHistory
    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    # Класс - отображение таблицы контактов пользователей
    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Класс - отображение таблицы истории действий
    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # Создаем движок БД
        # echo = False - отключение ведения лога (вывод sql-запросов)
        # pool-recycle - опция переустановки соединения
        print(path)
        self.database_engine = create_engine(f'sqlite:///{path}',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        # Создание объекта MetaData
        self.metadata = MetaData()

        # Таблица всех пользователей
        users_table = Table('Users',
                            self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        # Таблица активных пользователей
        active_users_table = Table('Active_users',
                                   self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        # Таблица истории входов
        user_login_history = Table('Login_history',
                                   self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        # Таблица контактов пользователей
        contacts = Table('Contacts',
                         self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        # Таблица истории пользователей
        users_history_table = Table('History',
                                    self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        # Команда создания таблиц
        self.metadata.create_all(self.database_engine)

        # Связываем класс в ORM с таблицей
        mapper_registry.map_imperatively(self.AllUsers, users_table)
        mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)
        mapper_registry.map_imperatively(self.LoginHistory, user_login_history)
        mapper_registry.map_imperatively(self.UsersContacts, contacts)
        mapper_registry.map_imperatively(self.UsersHistory, users_history_table)

        # Создаем сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Очищаем таблицу активных пользователей при установке соединения
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # При входе пользователя, формируем запись в БД факт входа
    def user_login(self, username, ip_address, port):
        print(username, ip_address, port)
        # Выбираем из таблицы AllUsers пользователя с таким именем
        rez = self.session.query(self.AllUsers).filter_by(name=username)
        # Если имя пользователя существует, обновляем время последнего входа
        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
        # Иначе создаем нового пользователя
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)
        self.session.commit()

    # При выходе пользователя, формируем запись в БД факт выхода
    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        # Получаем id отправителя и получателя
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счетчики
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1
        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()
        # Проверяем что контакт может существовать
        if not contact or \
            self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        # Создаем объект и заносим его в базу
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact:
            return

        # Удаляем требуемое
        print(
            self.session.query(self.UsersContacts).filter(
                self.UsersContacts.user == user.id,
                self.UsersContacts.contact == contact.id
            ).delete())
        self.session.commit()

    # Функция возвращает список известных пользователей со временем последнего входа
    def users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        )
        return query.all()

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()

    # Функция возвращает историю входа пользователя(ей)
    def login_history(self, username=None):
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    def get_contacts(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).one()
        query = self.session.query(self.UsersContacts, self.AllUsers.name). \
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)
        return [contact[1] for contact in query.all]

    def message_history(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)
        return query.all()


# Отладка
if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    print(test_db.users_list())
    # print(test_db.active_users_list())
    # test_db.user_logout('McG')
    # print(test_db.login_history('re'))
    # test_db.add_contact('test2', 'test1')
    # test_db.add_contact('test1', 'test3')
    # test_db.add_contact('test1', 'test6')
    # test_db.remove_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    print(test_db.message_history())
