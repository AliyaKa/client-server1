import datetime
import os.path

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import registry, sessionmaker

mapper_registry = registry()


class ClientDB:
    """
    Класс - оболочка для работы с базой данных клиента.
    Использует SQLite базу данных,
    реализован с помощью SQLAlchemy ORM и используется классический подход.
    """

    class KnownUsers:
        """
        Класс - отображение для таблицы всех пользователей
        """
        def __init__(self, user):
            self.id = None
            self.username = user

    # контакты
    class Contacts:
        """
        Класс - отображение для таблицы контактов
        """
        def __init__(self, contact):
            self.id = None
            self.name = contact

    class MessageStat:
        """
        Класс - отображение для таблицы статистики переданных сообщений
        """
        def __init__(self, contact, direction, message):
            self.id = None
            self.from_user = contact
            self.to_user = direction
            self.message = message
            self.datetime = datetime.datetime.now()

    # конструктор класса
    def __init__(self, name):
        # движок базы данных.
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
                        Column('contact', String),
                        Column('direction', String),
                        Column('message', Text),
                        Column('datetime', DateTime)
                        )
        # Запускаем создание таблиц
        self.metadata.create_all(self.database_engine)

        # Создаем отображения таблиц
        mapper_registry.map_imperatively(self.KnownUsers, users)
        mapper_registry.map_imperatively(self.Contacts, contacts)
        mapper_registry.map_imperatively(self.MessageStat, history)

        # Создаем сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Очищаем таблицу контактов, т.к. при запуске они загружаются с сервера
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_users(self, users):
        """Метод заполняющий таблицу известных пользователей."""
        # пользователей получаем с сервера, поэтому перед добавлением таблица очищается
        self.session.query(self.KnownUsers).delete()
        for user in users:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def add_contact(self, contact):
        """Метод добавляющий контакт в БД"""
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def get_contacts(self):
        """Метод возвращающий список всех контактов."""
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """Метод возвращающий список всех известных пользователей."""
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def get_history(self, contact):
        """Метод возвращающий историю сообщений с определённым пользователем."""
        query = self.session.query(self.MessageStat).filter_by(contact=contact)
        return [(history_row.contact,
                 history_row.direction,
                 history_row.message,
                 history_row.datetime)
                for history_row in query.all()]

    def del_contact(self, contact):
        """Метод удаляющий определённый контакт."""
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def contacts_clear(self):
        """Метод очищающий таблицу со списком контактов."""
        self.session.query(self.Contacts).delete()

    def save_message(self, contact, direction, message):
        """Метод сохраняющий сообщение в базе данных."""
        message_row = self.MessageStat(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def check_user(self, user):
        """Метод проверяющий существует ли пользователь."""
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        """Метод проверяющий существует ли контакт."""
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False


# отладка
if __name__ == '__main__':
    test_db = ClientDB('test1')
