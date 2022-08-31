import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Peer(Base):
    __tablename__ = 'peer'

    id = Column(Integer, primary_key=True, autoincrement=False)
    account = Column(JSON, nullable=False)
    info = Column(JSON, nullable=False)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=False)
    json = Column(JSON, nullable=False)
    date = Column(DateTime, nullable=False)

    def __init__(self, json):
        self.json = json
        self.id = json['id']
        self.date = datetime.datetime.fromtimestamp(json['date'])

        Base.__init__(self)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=False)
    json = Column(JSON, nullable=False)

    def __init__(self, json):
        self.json = json
        self.id = -json['id'] if 'name' in json else json['id']

        Base.__init__(self)


def connect(path):
    engine = create_engine(f'sqlite:///{path}', future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    return session
