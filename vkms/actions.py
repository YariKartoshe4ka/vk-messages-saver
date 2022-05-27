import logging
from os import listdir
from threading import Thread
from time import sleep

import vk

from . import attachments, messages, peers, saver, users
from .utils import dump_peer

logging.getLogger('vk').setLevel(logging.FATAL)


def dump(out_dir, include, exclude, token, nthreads):
    """
    Скачивает указанные переписки в формате JSON (результаты обращений к VK API)

    Args:
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
    peers_info = peers.download(api)

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
            messages.download(api, peer_id, peer)
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


def parse(out_dir, include, exclude, fmt):
    """
    Сохраняет полученные переписки в удобном для чтения формате

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        include (set): Множество идентификаторов переписок, которые нужно сохранить
        exclude (set): Множество идентификаторов переписок, которые не нужно сохранять
        fmt (str): Формат, в котором следует сохранять переписки
    """
    # Получаем идентификаторы всех скачанных переписок
    peer_ids = {int(file.rstrip('.json')) for file in listdir(f'{out_dir}/.json/')}

    # Выбираем нужные переписки
    if include:
        peer_ids &= include
    elif exclude:
        peer_ids -= exclude

    peer_ids_cnt = 0

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        print(f'{round(peer_ids_cnt / len(peer_ids) * 100)}%', end='\r')

        peer = peers.Peer(out_dir, peer_id)
        saver.save(out_dir, fmt, peer)
        peer_ids_cnt += 1

    print('100%')


def atch(out_dir, include, exclude, nthreads):
    """
    Скачивает вложения указанных переписок

    Args:
        out_dir (str): Абсолютный путь к каталогу, в котором находится
            результат работы программы
        include (set): Множество идентификаторов переписок, которые нужно обработать
        exclude (set): Множество идентификаторов переписок, которые не нужно обрабатывать
        nthreads (int): Количество потоков, загружающих вложения
    """
    # Получаем идентификаторы всех скачанных переписок
    peer_ids = {int(file.rstrip('.json')) for file in listdir(f'{out_dir}/.json/')}

    # Выбираем нужные переписки
    if include:
        peer_ids &= include
    elif exclude:
        peer_ids -= exclude

    peer_ids_cnt = 0

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        print(f'{round(peer_ids_cnt / len(peer_ids) * 100)}%', end='\r')

        peer = peers.Peer(out_dir, peer_id)
        attachments.download(out_dir, peer, nthreads)
        peer_ids_cnt += 1

    print('100%')
