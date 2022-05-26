from . import messages, users
from .utils import load_peer


def download(api):
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
    def __init__(self, out_dir, peer_id):
        peer = load_peer(out_dir, peer_id)
        usernames = users.parse(peer)

        self.info = peer['info']
        self.msgs = messages.parse(peer, usernames)
