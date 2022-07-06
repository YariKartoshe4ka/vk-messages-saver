import logging
from json import dumps
from os import listdir
from threading import Thread
from time import sleep

import vk
from vk.exceptions import VkAPIError

from . import attachments, messages, peers, saver, users


def dump(out_dir, include, exclude, token, nthreads, max_msgs):
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

        def get_captcha_key(self, request):
            return input(f'Captcha needed ({request.api_error.captcha_img}): ')

    api = API(access_token=token, v='5.131')

    # Загружаем информацию о владельце страницы
    try:
        account = api.users.get()[0]
    except VkAPIError:
        print('Failed to load base information. '
              f'See logs for details: {out_dir}/logs.txt')

        return

    # Загружаем информацию о всех переписках пользователя
    peers_info = peers.download(api)

    # Создаем словарь вида id-переписка для быстрого доступа к JSON'у конкретной переписки
    peer_by_id = {peer['peer']['id']: peer for peer in peers_info}

    # Создаем множество идентификаторов для последующей выборки нужных
    peer_ids = set(peer_by_id.keys())

    # Выбираем нужные переписки
    if include:
        peer_ids &= include
    elif exclude:
        peer_ids -= exclude

    peer_ids = list(peer_ids)
    peer_ids_len = len(peer_ids)

    logging.info(f"Peers: {', '.join(map(str, peer_ids))}")

    def dump_thread():
        """Поток для загрузки переписки"""

        # Работает, пока остались необработанные переписки
        while True:
            try:
                peer_id = peer_ids.pop()
            except IndexError:
                return

            logging.info(f'Processing peer {peer_id}')

            with open(f"{out_dir}/.json/{peer_id}.json", 'w', encoding='utf-8') as file:
                # Сохраняем информацию о переписке и владельце страницы
                print('###### PEER', file=file)

                print(dumps(account), file=file)
                print(dumps(peer_by_id[peer_id]), file=file)

                try:
                    # Сохраняем все сообщения и информацию об участниках переписки
                    print('###### MESSAGES', file=file)

                    user_ids = set()
                    group_ids = set()

                    for msg in messages.download(api, peer_id, max_msgs):
                        print(dumps(msg), file=file)
                        users.collect(msg, user_ids, group_ids)

                    if user_ids or group_ids:
                        print('###### USERS', file=file)

                        for user in users.download(api, user_ids, group_ids):
                            print(dumps(user), file=file)

                except VkAPIError as e:
                    logging.error(f'Downloading peer {peer_id} failed: {e}')
                    return

    # Список всех потоков
    tds = []

    # Создаем N потоков
    for _ in range(min(nthreads, peer_ids_len)):
        td = Thread(target=dump_thread, daemon=True)
        td.start()
        tds.append(td)

    # Ждем, пока все переписки будут скачаны
    n = sum(td.is_alive() for td in tds)
    while n:
        print(f'{round((peer_ids_len - len(peer_ids) - n) / peer_ids_len * 100)}%', end='\r')
        n = sum(td.is_alive() for td in tds)

    # Сливаем потоки
    for td in tds:
        td.join()

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

    processed = 0

    logging.info(f"Peers: {', '.join(map(str, peer_ids))}")

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        logging.info(f'Processing peer {peer_id}')

        print(f'{round(processed / len(peer_ids) * 100)}%', end='\r')

        try:
            peer = peers.Peer(out_dir, peer_id)
        except Exception:
            logging.error(f'Loading peer {peer_id} failed: JSON may be corrupted')
        else:
            saver.save(out_dir, fmt, peer)

        processed += 1

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

    logging.info(f"Peers: {', '.join(map(str, peer_ids))}")

    peer_ids_cnt = 0

    # Обрабатываем каждую переписку отдельно
    for peer_id in peer_ids:
        logging.info(f'Processing peer {peer_id}')

        print(f'{round(peer_ids_cnt / len(peer_ids) * 100)}%', end='\r')

        try:
            peer = peers.Peer(out_dir, peer_id)
        except Exception:
            logging.error(f'Loading peer {peer_id} failed: JSON may be corrupted')
        else:
            attachments.download(out_dir, peer, nthreads)

        peer_ids_cnt += 1

    print('100%')
