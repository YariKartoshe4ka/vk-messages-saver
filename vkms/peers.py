from json import dumps

from . import database as db
from . import messages, users


def download(api):
    """
    Загружает базовую информацию о всех переписках пользователя

    Args:
        api (vk.API): Объект, через который происходит обращение к
            методам VK API
    """
    # Получаем часть переписок
    res = api.messages.getConversations(count=200)
    peers = [item['conversation'] for item in res['items']]

    processed = len(peers)

    # Повторяем действия выше, пока все переписки не будут загружены
    while processed < res['count']:
        res = api.messages.getConversations(offset=processed, count=200)
        peers += [item['conversation'] for item in res['items']]

    return peers


def export_json(out_dir, session):
    """
    Экспортирует данные из SQLite в немного модифицированный JSON

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        session: Открытая сессия к БД нужной переписки
    """
    peer = session.query(db.Peer).one()

    with open(out_dir / f'.json/{peer.id}.json', 'w') as file:
        # Экспортируем информацию о переписке и владельце
        print(f"{'-' * 6} PEER {'-' * 6}", file=file)
        print(dumps(peer.account), file=file)
        print(dumps(peer.info), file=file)

        # Экспортируем все сообщения
        print(f"{'-' * 6} MESSAGES {'-' * 6}", file=file)

        for msg_json, in session.query(db.Message.json).yield_per(5000):
            print(dumps(msg_json), file=file)

        # Экспортируем всех участников
        print(f"{'-' * 6} USERS {'-' * 6}", file=file)

        for user_json, in session.query(db.User.json).yield_per(5000):
            print(dumps(user_json), file=file)


class Peer:
    """
    Класс для представления всей переписки пользователя из JSON

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        peer_id (int): Идентификатор переписки, которую нужно представить
    """

    def __init__(self, session):
        # Загружаем и сохраняем информацию о переписке из JSON
        self.account, self.info = session.query(db.Peer.account, db.Peer.info).one()

        usernames = users.parse(session)

        # Парсим все сообщения переписки
        self.msgs = messages.MessagesFactory(session, usernames).parse()

        # Сохраняем название переписки
        if self.info['peer']['type'] == 'chat':
            self.title = self.info['chat_settings']['title']
        else:
            self.title = usernames[self.info['peer']['id']]
