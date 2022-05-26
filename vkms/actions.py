import logging
from threading import Thread
from time import sleep

import vk

from . import attachments, messages, peers, saver, users
from .utils import dump_peer

logging.getLogger('vk').setLevel(logging.FATAL)


def dump(base_dir, out_dir, include, exclude, token, nthreads):
    """
    Скачивает указанные переписки в формате JSON (результаты обращений к VK API)

    Args:
        base_dir (str): Абсолютный путь к каталогу, в котором находится файл
            с основной точкой входа скрипта
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        include (set): Множество идентификаторов переписок, которые нужно сохранить
        exclude (set): Множество идентификаторов переписок, которые не нужно сохранять
        token (str): Токен доступа к VK API
        nthreads (int): Количество потоков, загружающих переписки
    """
    # Получаем объект для работы с VK API
    class API(vk.API):
        def on_api_error_6(self, request):
            sleep(1)
            return self.send(request)

    api = API(access_token=token, v='5.131')

    # Загружаем информацию о всех переписках пользователя
    peers_info = peers.download(base_dir, api)

    # Создаем словарь вида id-переписка для быстрого доступа к JSON'у конкретной переписки
    peer_by_id = {peer['peer']['id']: peer for peer in peers_info}

    # Создаем множество идентификаторов для последующей выборки нужных
    peer_ids = set(peer_by_id.keys())

    # Загружаем информацию о владельце страницы
    account = api.users.get()[0]

    # Выбираем нужные переписки
    if include:
        peer_ids &= include

    elif exclude:
        peer_ids -= exclude

    peer_ids = list(peer_ids)
    peer_ids_len = len(peer_ids)

    def dump_thread():
        """Поток для загрузки переписки"""

        # Работает, пока остались необработанные переписки
        while True:
            try:
                peer_id = peer_ids.pop()
            except IndexError:
                return

            # Сохраняем информацию о переписке и владельце страницы
            peer = {'info': peer_by_id[peer_id]}
            peer['info']['account'] = account

            # Сохраняем все сообщения и информацию об участниках переписки
            messages.download(base_dir, api, peer_id, peer)
            users.download(api, peer)

            # Записываем все в JSON
            dump_peer(out_dir, peer_id, peer)

    # Список всех потоков
    tds = []

    # Создаем N потоков
    for _ in range(nthreads):
        td = Thread(target=dump_thread, daemon=True)
        td.start()
        tds.append(td)

    # Ждем, пока все переписки будут скачаны
    while peer_ids:
        print(f'{round((peer_ids_len - len(peer_ids)) / peer_ids_len * 100)}%', end='\r')

    print('100%')


def parse(out_dir, peer_id, fmt):
    peer = peers.Peer(out_dir, peer_id)
    saver.save(out_dir, fmt, peer)


def atch(out_dir, peer_id):
    peer = peers.Peer(out_dir, peer_id)
    attachments.download(out_dir, peer)
