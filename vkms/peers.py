from . import messages, users
from .utils import load_peer


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


class Peer:
    """
    Класс для представления всей переписки пользователя из JSON

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        peer_id (int): Идентификатор переписки, которую нужно представить
    """

    def __init__(self, out_dir, peer_id):
        # Загружаем всю информацию из JSON
        peer = load_peer(out_dir, peer_id)

        usernames = users.parse(peer)

        # Сохраняем информацию о переписке
        self.info = peer['info']

        # Парсим все сообщения переписки
        self.msgs = messages.parse(peer, usernames)

        # Сохраняем название переписки
        if self.info['peer']['type'] == 'chat':
            self.title = self.info['chat_settings']['title']
        else:
            self.title = usernames[self.info['peer']['id']]
