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

    def __init__(self):
        # Создаем движок БД
        # echo = False - отключение ведения лога (вывод sql-запросов)
        # pool-recycle - опция переустановки соединения
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)

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

        # Команда создания таблиц
        self.metadata.create_all(self.database_engine)

        # Связываем класс в ORM с таблицей
        mapper_registry.map_imperatively(self.AllUsers, users_table)
        mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)
        mapper_registry.map_imperatively(self.LoginHistory, user_login_history)

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


if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('client1', '192.168.1.4', 8888)
    test_db.user_login('client2', '192.168.1.5', 7777)
    print(test_db.active_users_list())
    test_db.user_logout('client1')
    print(test_db.active_users_list())
    test_db.login_history('client1')
    print(test_db.users_list())
