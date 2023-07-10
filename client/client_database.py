import datetime
import os.path

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import registry, sessionmaker
import sys
sys.path.append('../')
mapper_registry = registry()


class ClientDB:
    # известные пользователи
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    # контакты
    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    # история сообщений
    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.datetime = datetime.datetime.now()

    # движок БД, каждый клиент будет иметь свою БД
    def __init__(self, name):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.database_engine = create_engine(f'sqlite:///{os.path.join(path, filename)}',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        # Создаем объект Metadata
        self.metadata = MetaData()

        # Таблица известных пользователей
        users = Table('known_users',
                      self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )
        # Таблица контактов
        contacts = Table('contacts',
                         self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )
        # Таблица история сообщений
        history = Table('msg_history',
                        self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_user', String),
                        Column('to_user', String),
                        Column('message', Text),
                        Column('datetime', DateTime)
                        )
        # Запускаем создание таблиц
        self.metadata.create_all(self.database_engine)

        # Создаем отображения таблиц
        mapper_registry.map_imperatively(self.KnownUsers, users)
        mapper_registry.map_imperatively(self.Contacts, contacts)
        mapper_registry.map_imperatively(self.MessageHistory, history)

        # Создаем сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Очищаем таблицу контактов, т.к. при запуске они загружаются с сервера
        self.session.query(self.Contacts).delete()
        self.session.commit()

    # Функционал:
    # - добавление пользователей в таблицу users:
    def add_users(self, users):
        # пользователей получаем с сервера, поэтому перед добавлением таблица очищается
        self.session.query(self.KnownUsers).delete()
        for user in users:
            self.session.add(self.KnownUsers(user))
        self.session.commit()

    # - добавление контактов:
    def add_contact(self, contact):
        # Если в таблице контактов нет данного пользователя, добавляем запись
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            self.session.add(self.Contacts(contact))
            self.session.commit()

    # - возвращает список контактов
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # - возвращает список известных пользователей
    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    # - возвращает историю переписки
    def get_history(self, from_who=None, to_who=None):
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user,
                 history_row.to_user,
                 history_row.message,
                 history_row.datetime)
                for history_row in query.all()]

    # - удаление контактов:
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    # - сохранение сообщений
    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    # - проверка на наличие пользователя в известных
    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    # - проверка на наличие пользователя в контактах
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False


# отладка
if __name__ == '__main__':
    test_db = ClientDB('test1')
    print(sorted(test_db.get_history('test2'), key=lambda item: item[3]))
